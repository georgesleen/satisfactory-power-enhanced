#include "EnhancedPowerProbe.h"

#include "Containers/UnrealString.h"
#include "Engine/World.h"
#include "FGCircuitSubsystem.h"
#include "HAL/IConsoleManager.h"
#include "Misc/OutputDevice.h"
#include "Modules/ModuleManager.h"
#include "Patching/NativeHookManager.h"

namespace
{
TWeakObjectPtr<AEnhancedPowerTransformerProbe> ActiveProbe;
constexpr double DefaultRating = 50.0;
constexpr int32 ConfigurationArguments = 4;

bool IsServerWorld(UWorld* World, FOutputDevice& Output)
{
	if (!World || !World->IsGameWorld() || World->GetNetMode() == NM_Client || WITH_EDITOR)
	{
		Output.Log(TEXT("EnhancedPower probe requires a non-editor authoritative game world."));
		return false;
	}
	return true;
}

bool ParseNonnegative(const FString& Argument, double& Value)
{
	return LexTryParseString(Value, *Argument) && FMath::IsFinite(Value) && Value >= 0.0 &&
	       Value <= static_cast<double>(MAX_flt);
}

bool HasProbe(UWorld* World, FOutputDevice& Output)
{
	if (!IsServerWorld(World, Output))
	{
		return false;
	}
	if (!ActiveProbe.IsValid() || ActiveProbe->GetWorld() != World)
	{
		Output.Log(TEXT("No EnhancedPower probe in this world."));
		return false;
	}
	return true;
}

void Start(const TArray<FString>& Arguments, UWorld* World, FOutputDevice& Output)
{
	if (!IsServerWorld(World, Output))
	{
		return;
	}
	double Rating = DefaultRating;
	if (Arguments.Num() > 1 || (Arguments.Num() == 1 && !ParseNonnegative(Arguments[0], Rating)) ||
	    Rating <= 0.0 || Rating > static_cast<double>(MAX_flt) / 2.0)
	{
		Output.Log(TEXT("Usage: EnhancedPower.Probe.Start [positiveRatingMW]"));
		return;
	}
	if (ActiveProbe.IsValid() && ActiveProbe->GetWorld() != World)
	{
		ActiveProbe.Reset();
	}
	if (ActiveProbe.IsValid())
	{
		Output.Log(TEXT("Stop the active probe before starting another."));
		return;
	}
	if (!AFGCircuitSubsystem::Get(World))
	{
		Output.Log(TEXT("Circuit subsystem is not ready."));
		return;
	}
	FActorSpawnParameters Parameters;
	Parameters.ObjectFlags |= RF_Transient;
	Parameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	auto* Probe = World->SpawnActor<AEnhancedPowerTransformerProbe>(FVector::ZeroVector,
	                                                                FRotator::ZeroRotator, Parameters);
	if (!Probe || !Probe->Initialize(Rating))
	{
		if (Probe)
		{
			Probe->Destroy();
		}
		Output.Log(TEXT("EnhancedPower probe spawn failed; inspect LogEnhancedPower."));
		return;
	}
	ActiveProbe = Probe;
	Output.Log(TEXT("EnhancedPower probe starts unloaded. Wait for funded escrow, then use "
	                "EnhancedPower.Probe.Set. Logs: LogEnhancedPower."));
}

void Configure(const TArray<FString>& Arguments, UWorld* World, FOutputDevice& Output)
{
	if (!HasProbe(World, Output))
	{
		return;
	}
	double Values[ConfigurationArguments]{};
	bool bValid = Arguments.Num() == ConfigurationArguments;
	for (int32 Index = 0; bValid && Index < ConfigurationArguments; Index++)
	{
		bValid = ParseNonnegative(Arguments[Index], Values[Index]);
	}
	if (!bValid)
	{
		Output.Log(TEXT("Usage: EnhancedPower.Probe.Set sourceMW loadMW peakMW periodSeconds (nonnegative, "
		                "period 0 disables pulse)"));
		return;
	}
	if (ActiveProbe->Configure(Values[0], Values[1], Values[2], Values[3]))
	{
		Output.Log(TEXT("EnhancedPower probe source and load configured. "
		                "Fuses remain latched; Stop/Start resets fixture."));
	}
	else
	{
		Output.Log(TEXT("EnhancedPower probe fixtures are unavailable; Stop/Start resets fixture."));
	}
}

void Stop(const TArray<FString>& Arguments, UWorld* World, FOutputDevice& Output)
{
	if (!HasProbe(World, Output))
	{
		return;
	}
	ActiveProbe->Report();
	ActiveProbe->Destroy();
	ActiveProbe.Reset();
	Output.Log(TEXT("EnhancedPower probe stopped; transient fixture destroyed."));
}

void Report(const TArray<FString>& Arguments, UWorld* World, FOutputDevice& Output)
{
	if (HasProbe(World, Output))
	{
		ActiveProbe->Report();
		Output.Log(TEXT("EnhancedPower probe report written to LogEnhancedPower."));
	}
}

FAutoConsoleCommandWithWorldArgsAndOutputDevice
    StartCommand(TEXT("EnhancedPower.Probe.Start"), TEXT("Spawn a transient unloaded probe: [ratingMW]."),
                 FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateStatic(&Start));
FAutoConsoleCommandWithWorldArgsAndOutputDevice
    ConfigureCommand(TEXT("EnhancedPower.Probe.Set"), TEXT("Set sourceMW loadMW peakMW periodSeconds."),
                     FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateStatic(&Configure));
FAutoConsoleCommandWithWorldArgsAndOutputDevice
    StopCommand(TEXT("EnhancedPower.Probe.Stop"), TEXT("Report and destroy the transient probe."),
                FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateStatic(&Stop));
FAutoConsoleCommandWithWorldArgsAndOutputDevice
    ReportCommand(TEXT("EnhancedPower.Probe.Report"), TEXT("Log cumulative energy accounting."),
                  FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateStatic(&Report));
} // namespace

class FEnhancedPowerModule : public IModuleInterface
{
public:
	virtual void StartupModule() override
	{
#if !WITH_EDITOR
		BeforeHandle = SUBSCRIBE_UOBJECT_METHOD(
		    AFGCircuitSubsystem, Tick,
		    [](auto& Scope, AFGCircuitSubsystem* Subsystem, float DeltaSeconds)
		    {
			    if (ActiveProbe.IsValid() && ActiveProbe->GetWorld() == Subsystem->GetWorld() &&
			        Subsystem->HasAuthority())
			    {
				    ActiveProbe->BeforeSolve(DeltaSeconds);
			    }
		    });
		AfterHandle = SUBSCRIBE_UOBJECT_METHOD_AFTER(
		    AFGCircuitSubsystem, Tick,
		    [](AFGCircuitSubsystem* Subsystem, float DeltaSeconds)
		    {
			    if (ActiveProbe.IsValid() && ActiveProbe->GetWorld() == Subsystem->GetWorld() &&
			        Subsystem->HasAuthority())
			    {
				    ActiveProbe->AfterSolve(DeltaSeconds);
			    }
		    });
#endif
	}

	virtual void ShutdownModule() override
	{
#if !WITH_EDITOR
		UNSUBSCRIBE_UOBJECT_METHOD(AFGCircuitSubsystem, Tick, BeforeHandle);
		UNSUBSCRIBE_UOBJECT_METHOD(AFGCircuitSubsystem, Tick, AfterHandle);
#endif
		ActiveProbe.Reset();
	}

private:
	FDelegateHandle BeforeHandle;
	FDelegateHandle AfterHandle;
};

IMPLEMENT_MODULE(FEnhancedPowerModule, EnhancedPower)
