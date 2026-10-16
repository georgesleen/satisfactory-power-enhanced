#include "EnhancedPowerProbe.h"

#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "FGCircuitSubsystem.h"
#include "FGPowerCircuit.h"
#include "FGPowerConnectionComponent.h"
#include <cmath>

DEFINE_LOG_CATEGORY(LogEnhancedPower);

namespace
{
constexpr double SourceHeadroom = 2.0;
constexpr double EscrowSeconds = 0.25;
constexpr double PulseDutyFraction = 0.5;

double EnginePower(double Value)
{
	float Rounded = static_cast<float>(Value);
	if (static_cast<double>(Rounded) > Value)
	{
		Rounded = std::nextafter(Rounded, 0.0f);
	}
	return Rounded;
}
constexpr double ConservationTolerance = 0.000001;
} // namespace

void UEnhancedPowerProbeInfo::BeginInterval()
{
	Callbacks = 0;
	bInsideInterval = true;
}

void UEnhancedPowerProbeInfo::EndInterval()
{
	bInsideInterval = false;
}

void UEnhancedPowerProbeInfo::UpdateSimulationData(float DemandFactor, float Consumption, bool bFuseTriggered,
                                                   bool bHasPower, float ProductionBoost)
{
	if (bInsideInterval)
	{
		Callbacks++;
	}
	else
	{
		OutsideCallbacks++;
	}
	Super::UpdateSimulationData(DemandFactor, Consumption, bFuseTriggered, bHasPower, ProductionBoost);
}

AEnhancedPowerProbeFixture::AEnhancedPowerProbeFixture()
{
	PrimaryActorTick.bCanEverTick = false;
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
	Connection = CreateDefaultSubobject<UFGPowerConnectionComponent>(TEXT("Connection"));
	Connection->SetupAttachment(GetRootComponent());
	Connection->SetIsHidden(true);
	PowerInfo = CreateDefaultSubobject<UEnhancedPowerProbeInfo>(TEXT("PowerInfo"));
}

void AEnhancedPowerProbeFixture::BeginPlay()
{
	Super::BeginPlay();
	Connection->SetPowerInfo(PowerInfo);
}

AEnhancedPowerTransformerProbe::AEnhancedPowerTransformerProbe()
{
	PrimaryActorTick.bCanEverTick = false;
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
	Primary = CreateDefaultSubobject<UFGPowerConnectionComponent>(TEXT("Primary"));
	Secondary = CreateDefaultSubobject<UFGPowerConnectionComponent>(TEXT("Secondary"));
	Primary->SetupAttachment(GetRootComponent());
	Secondary->SetupAttachment(GetRootComponent());
	PrimaryInfo = CreateDefaultSubobject<UEnhancedPowerProbeInfo>(TEXT("PrimaryInfo"));
	SecondaryInfo = CreateDefaultSubobject<UEnhancedPowerProbeInfo>(TEXT("SecondaryInfo"));
}

void AEnhancedPowerTransformerProbe::BeginPlay()
{
	Super::BeginPlay();
	Primary->SetPowerInfo(PrimaryInfo);
	Secondary->SetPowerInfo(SecondaryInfo);
}

bool AEnhancedPowerTransformerProbe::Initialize(double Rating)
{
	Parameters = {{Rating}, 1.0, {Rating * EscrowSeconds}, {Rating}};
	FActorSpawnParameters SpawnParameters;
	SpawnParameters.ObjectFlags |= RF_Transient;
	SpawnParameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Source = GetWorld()->SpawnActor<AEnhancedPowerProbeFixture>(FVector::ZeroVector, FRotator::ZeroRotator,
	                                                            SpawnParameters);
	Load = GetWorld()->SpawnActor<AEnhancedPowerProbeFixture>(FVector::ZeroVector, FRotator::ZeroRotator,
	                                                          SpawnParameters);
	if (!Source || !Load)
	{
		UE_LOG(LogEnhancedPower, Error, TEXT("Probe fixture spawn failed"));
		return false;
	}
	Source->Connection->AddHiddenConnection(Primary);
	Secondary->AddHiddenConnection(Load->Connection);
	return Configure(Rating * SourceHeadroom, 0.0, 0.0, 0.0);
}

bool AEnhancedPowerTransformerProbe::Configure(double SourceProduction, double LoadConsumption,
                                               double PeakConsumption, double Period)
{
	if (!IsValid(Source) || !IsValid(Load))
	{
		UE_LOG(LogEnhancedPower, Error, TEXT("Probe configuration requires valid source and load fixtures"));
		return false;
	}
	Source->PowerInfo->SetBaseProduction(static_cast<float>(SourceProduction));
	BaselineConsumption = LoadConsumption;
	PulseConsumption = PeakConsumption;
	PulsePeriod = Period;
	Elapsed = 0.0;
	return true;
}
void AEnhancedPowerTransformerProbe::BeforeSolve(float DeltaSeconds)
{
	if (!HasAuthority() || !IsValid(Source) || !IsValid(Load) || bPending)
	{
		return;
	}
	PrimaryInfo->BeginInterval();
	SecondaryInfo->BeginInterval();
	Source->PowerInfo->BeginInterval();
	Load->PowerInfo->BeginInterval();
	Elapsed += DeltaSeconds;
	const bool bPulse =
	    PulsePeriod > 0.0 && FMath::Fmod(Elapsed, PulsePeriod) >= PulsePeriod * PulseDutyFraction;
	Load->PowerInfo->SetTargetConsumption(
	    static_cast<float>(bPulse ? PulseConsumption : BaselineConsumption));
	const bool bPrimaryAvailable = Primary->HasPower() && !PrimaryInfo->IsFuseTriggered();
	Plan = EnhancedPower::PlanLink(Parameters, State, {DeltaSeconds}, bPrimaryAvailable);
	if (ThermalState.Tripped)
	{
		Plan.SecondaryOffer = {0.0};
		Plan.PrimaryRequest = {0.0};
	}
	Plan.PrimaryRequest.Value = EnginePower(Plan.PrimaryRequest.Value);
	Plan.SecondaryOffer.Value = EnginePower(Plan.SecondaryOffer.Value);
	PreSolveRequest = PrimaryInfo->GetTargetConsumption();
	PrimaryInfo->SetTargetConsumption(static_cast<float>(Plan.PrimaryRequest.Value));
	SecondaryInfo->SetDynamicProductionCapacity(static_cast<float>(Plan.SecondaryOffer.Value));
	bPending = true;
}

void AEnhancedPowerTransformerProbe::AfterSolve(float DeltaSeconds)
{
	if (!bPending || !IsValid(Source) || !IsValid(Load))
	{
		return;
	}
	bPending = false;
	PrimaryInfo->EndInterval();
	SecondaryInfo->EndInterval();
	Source->PowerInfo->EndInterval();
	Load->PowerInfo->EndInterval();
	const double Consumed = PrimaryInfo->GetActualConsumption();
	const double Delivered = SecondaryInfo->GetRegulatedDynamicProduction();
	const auto Settlement =
	    EnhancedPower::SettleLink(Parameters, State, Plan, {DeltaSeconds}, {Consumed}, {Delivered});
	State = Settlement.State;
	ThermalState = EnhancedPower::StepThermal(ThermalParameters, ThermalState,
	                                          Delivered / Parameters.Rating.Value, {DeltaSeconds});
	InputEnergy += Consumed * DeltaSeconds;
	OutputEnergy += Delivered * DeltaSeconds;
	LostEnergy += Settlement.Loss.Value;
	OverflowEnergy += Settlement.Overflow.Value;
	OverDeliveryEnergy += Settlement.OverDelivery.Value;
	OverConsumptionEnergy += Settlement.OverConsumption.Value;
	Intervals++;
	UFGPowerCircuit* PrimaryCircuit = Primary->GetPowerCircuit();
	UFGPowerCircuit* SecondaryCircuit = Secondary->GetPowerCircuit();
	UE_LOG(LogEnhancedPower, Log,
	       TEXT("Probe tick=%llu dt=%.9g circuit=%d,%d group=%d,%d planRequest=%.9g "
	            "preSolveRequest=%.9g planOffer=%.9g request=%.9g capacity=%.9g "
	            "consumed=%.9g delivered=%.9g factor=%.9g source=%.9g "
	            "loadTarget=%.9g loadActual=%.9g power=%d,%d fuse=%d,%d heat=%.9g trip=%d loss=%.9g "
	            "overflow=%.9g overDelivery=%.9g overConsumption=%.9g escrow=%.9g "
	            "callbacks=%llu,%llu,%llu,%llu outside=%llu,%llu,%llu,%llu"),
	       Intervals, DeltaSeconds, Primary->GetCircuitID(), Secondary->GetCircuitID(),
	       PrimaryCircuit ? PrimaryCircuit->GetCircuitGroupID() : INDEX_NONE,
	       SecondaryCircuit ? SecondaryCircuit->GetCircuitGroupID() : INDEX_NONE, Plan.PrimaryRequest.Value,
	       PreSolveRequest, Plan.SecondaryOffer.Value, PrimaryInfo->GetTargetConsumption(),
	       SecondaryInfo->GetDynamicProductionCapacity(), Consumed, Delivered,
	       SecondaryInfo->GetDynamicProductionDemandFactor(), Source->PowerInfo->GetBaseProduction(),
	       Load->PowerInfo->GetTargetConsumption(), Load->PowerInfo->GetActualConsumption(),
	       PrimaryInfo->HasPower(), SecondaryInfo->HasPower(),
	       PrimaryCircuit ? PrimaryCircuit->IsFuseTriggered() : false,
	       SecondaryCircuit ? SecondaryCircuit->IsFuseTriggered() : false, ThermalState.Heat,
	       ThermalState.Tripped, Settlement.Loss.Value, Settlement.Overflow.Value,
	       Settlement.OverDelivery.Value, Settlement.OverConsumption.Value, State.Escrow.Value,
	       PrimaryInfo->Callbacks, SecondaryInfo->Callbacks, Source->PowerInfo->Callbacks,
	       Load->PowerInfo->Callbacks, PrimaryInfo->OutsideCallbacks, SecondaryInfo->OutsideCallbacks,
	       Source->PowerInfo->OutsideCallbacks, Load->PowerInfo->OutsideCallbacks);
}

void AEnhancedPowerTransformerProbe::Report() const
{
	const double Residual = InputEnergy - OutputEnergy - LostEnergy - OverflowEnergy - State.Escrow.Value;
	UE_LOG(LogEnhancedPower, Log,
	       TEXT("Probe report ticks=%llu inputMJ=%.12g outputMJ=%.12g lossMJ=%.12g overflowMJ=%.12g "
	            "escrowMJ=%.12g overDeliveryMJ=%.12g overConsumptionMJ=%.12g residualMJ=%.12g conserved=%d"),
	       Intervals, InputEnergy, OutputEnergy, LostEnergy, OverflowEnergy, State.Escrow.Value,
	       OverDeliveryEnergy, OverConsumptionEnergy, Residual,
	       FMath::Abs(Residual) <= ConservationTolerance && OverDeliveryEnergy == 0.0 &&
	           OverConsumptionEnergy == 0.0);
}

void AEnhancedPowerTransformerProbe::EndPlay(const EEndPlayReason::Type Reason)
{
	PrimaryInfo->SetTargetConsumption(0.0f);
	SecondaryInfo->SetDynamicProductionCapacity(0.0f);
	if (Reason == EEndPlayReason::Destroyed)
	{
		const bool bHasSubsystem = IsValid(AFGCircuitSubsystem::Get(GetWorld()));
		if (IsValid(Source))
		{
			if (bHasSubsystem)
			{
				Source->Connection->RemoveHiddenConnection(Primary);
			}
			Source->Destroy();
		}
		if (IsValid(Load))
		{
			if (bHasSubsystem)
			{
				Secondary->RemoveHiddenConnection(Load->Connection);
			}
			Load->Destroy();
		}
	}
	Super::EndPlay(Reason);
}
