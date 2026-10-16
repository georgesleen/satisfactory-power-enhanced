#pragma once

#include "CoreMinimal.h"
#include "EnhancedPowerCore/Thermal.h"
#include "EnhancedPowerCore/TransformerLink.h"
#include "FGPowerInfoComponent.h"
#include "GameFramework/Actor.h"

#include "EnhancedPowerProbe.generated.h"

class UFGPowerConnectionComponent;

DECLARE_LOG_CATEGORY_EXTERN(LogEnhancedPower, Log, All);

// A power info that counts solver callbacks within each subsystem tick.
UCLASS(Transient, NotBlueprintable)
class ENHANCEDPOWER_API UEnhancedPowerProbeInfo : public UFGPowerInfoComponent
{
	GENERATED_BODY()
public:
	void BeginInterval();
	void EndInterval();
	uint64 Callbacks = 0;
	uint64 OutsideCallbacks = 0;

private:
	bool bInsideInterval = false;
	virtual void UpdateSimulationData(float DemandFactor, float Consumption, bool bFuseTriggered,
	                                  bool bHasPower, float ProductionBoost) override;
};

// A transient source or load endpoint for the diagnostic circuit.
UCLASS(Transient, NotBlueprintable)
class ENHANCEDPOWER_API AEnhancedPowerProbeFixture : public AActor
{
	GENERATED_BODY()
public:
	AEnhancedPowerProbeFixture();
	virtual void BeginPlay() override;
	UPROPERTY()
	TObjectPtr<UFGPowerConnectionComponent> Connection;
	UPROPERTY()
	TObjectPtr<UEnhancedPowerProbeInfo> PowerInfo;
};

// A transient directional transformer between two independent test circuits.
UCLASS(Transient, NotBlueprintable)
class ENHANCEDPOWER_API AEnhancedPowerTransformerProbe : public AActor
{
	GENERATED_BODY()
public:
	AEnhancedPowerTransformerProbe();
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
	bool Initialize(double Rating);
	bool Configure(double SourceProduction, double LoadConsumption, double PeakConsumption, double Period);
	void BeforeSolve(float DeltaSeconds);
	void AfterSolve(float DeltaSeconds);
	void Report() const;

private:
	UPROPERTY()
	TObjectPtr<UFGPowerConnectionComponent> Primary;
	UPROPERTY()
	TObjectPtr<UFGPowerConnectionComponent> Secondary;
	UPROPERTY()
	TObjectPtr<UEnhancedPowerProbeInfo> PrimaryInfo;
	UPROPERTY()
	TObjectPtr<UEnhancedPowerProbeInfo> SecondaryInfo;
	UPROPERTY()
	TObjectPtr<AEnhancedPowerProbeFixture> Source;
	UPROPERTY()
	TObjectPtr<AEnhancedPowerProbeFixture> Load;

	EnhancedPower::LinkParameters Parameters;
	EnhancedPower::LinkState State;
	EnhancedPower::LinkPlan Plan;
	EnhancedPower::ThermalParameters ThermalParameters{{10.0}, 1.0, 1.44};
	EnhancedPower::ThermalState ThermalState;
	double BaselineConsumption = 0.0;
	double PulseConsumption = 0.0;
	double PulsePeriod = 0.0;
	double Elapsed = 0.0;
	double PreSolveRequest = 0.0;
	double InputEnergy = 0.0;
	double OutputEnergy = 0.0;
	double LostEnergy = 0.0;
	double OverflowEnergy = 0.0;
	double OverDeliveryEnergy = 0.0;
	double OverConsumptionEnergy = 0.0;
	uint64 Intervals = 0;
	bool bPending = false;
};
