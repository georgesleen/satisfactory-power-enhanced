using UnrealBuildTool;

public class EnhancedPowerCore : ModuleRules
{
	public EnhancedPowerCore(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.NoPCHs;
		CppStandard = CppStandardVersion.Cpp20;
		bUseUnity = false;
		PrivateDependencyModuleNames.Add("Core");
	}
}
