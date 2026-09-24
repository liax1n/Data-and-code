#1----调用包
import os
import numpy as np
from parflow import Run
import shutil
from parflow.tools.fs import mkdir, cp, get_absolute_path, exists, rm
from parflow.tools.settings import set_working_directory

#2----基础设置
# Name your ParFLow run -- note that all of your output files will have this prefix
runname = 'mao'

# Create a directory in the outputs folder for this run
run_dir = get_absolute_path(f'step_33')
mkdir(run_dir)
print(run_dir)

# create your Parflow model object. For starters we are just goin to set the file version and the run directory we'll add more later
# note that the model will run from the run_dir so all input files should be in the run dir or paths should be specified relative to run_dir
model = Run(runname, run_dir)
model.FileVersion = 4

# 获取路径
current_dir = os.getcwd()
parent_dir = os.path.dirname(current_dir)
pfb_dir = os.path.join(parent_dir, 'pfb_files')
clm_dir = os.path.join(parent_dir, 'clm_input')
step_dir = os.path.join(current_dir, 'step_32')

# 设置为 ParFlow 实际运行目录
run_dir = os.path.join(current_dir, 'step_33')
os.makedirs(run_dir, exist_ok=True)

# === 复制并重命名pfb文件 ===
special_files = {'mannings2019_new.pfb': 'mannings.pfb',
                 'slopex.pfb': 'slopex.pfb',
                 'slopey.pfb': 'slopey.pfb',
                 'IndicatorFile.pfb': 'IndicatorFile.pfb',
                 'DTB.pfb': 'DTB.pfb'}
for src_name, dst_name in special_files.items():
    src = os.path.join(pfb_dir, src_name)
    dst = os.path.join(run_dir, dst_name)
    if os.path.exists(src):
        shutil.copy(src, dst)
        print(f"copy as: {dst_name}")
    else:
        print(f"error: {src_name}")

# === 复制并重命名pfb文件 ===
special_files = {
    'mao.out.press.00366.pfb': 'press.init.pfb',
    'mao.out.press.00366.pfb.dist': 'press.init.pfb.dist'
}
for src_name, dst_name in special_files.items():
    src = os.path.join(step_dir, src_name)
    dst = os.path.join(run_dir, dst_name)
    if os.path.exists(src):
        shutil.copy(src, dst)
        print(f"copy as: {dst_name}")
    else:
        print(f"error: {src_name}")

# === 复制并重命名clm文件 ===
clm_files = {
    'drv_clmin.dat': 'drv_clmin.dat',
    'drv_vegp.dat': 'drv_vegp.dat',
    'drv_vegm.alluv2019.dat': 'drv_vegm.alluv.dat'
}
for src_name, dst_name in clm_files.items():
    src = os.path.join(clm_dir, src_name)
    dst = os.path.join(run_dir, dst_name)
    if os.path.exists(src):
        shutil.copy(src, dst)
        print(f"copy as: {dst_name}")
    else:
        print(f"error: {src_name}")

#3.1----基础网格
# Processor topology: This is the way that the problem will be split across processors if you want to run in parallel
# The domain is divided in x,y and z dimensions by P, Q and R. The total number of processors is P*Q*R.
model.Process.Topology.P = 11
model.Process.Topology.Q = 5
model.Process.Topology.R = 1

model.ComputationalGrid.Lower.X = 0.0
model.ComputationalGrid.Lower.Y = 0.0
model.ComputationalGrid.Lower.Z = 0.0

model.ComputationalGrid.DX = 1000.0
model.ComputationalGrid.DY = 1000.0
model.ComputationalGrid.DZ = 20.0

# Define the number of grid blocks in the domain.
model.ComputationalGrid.NX = 330
model.ComputationalGrid.NY = 200
model.ComputationalGrid.NZ = 10

#3.2----地质单元
#Declare the geometries that you will use for the problem
model.GeomInput.Names = "box_input indi_input"

#Define the solid_input geometry.
#Note the naming convention here GeomInput.{GeomName}.key
model.GeomInput.box_input.InputType = "Box"
model.GeomInput.box_input.GeomName = 'domain'
# model.GeomInput.solid_input.FileName = "LW.pfsol"

# Next setup the indicator file geometry
model.GeomInput.indi_input.InputType = "IndicatorField"
model.GeomInput.indi_input.GeomNames = "s1 s2 s3 s4 s5 s6 s7 s8 s9 g1 g2 g3 g4 g5 g6 g7 g8 g9"
model.Geom.indi_input.FileName = "IndicatorFile.pfb"

model.GeomInput.s1.Value = 1
model.GeomInput.s2.Value = 2
model.GeomInput.s3.Value = 3
model.GeomInput.s4.Value = 4
model.GeomInput.s5.Value = 5
model.GeomInput.s6.Value = 6
model.GeomInput.s7.Value = 7
model.GeomInput.s8.Value = 8
model.GeomInput.s9.Value = 9

model.GeomInput.g1.Value = 21
model.GeomInput.g2.Value = 22
model.GeomInput.g3.Value = 23
model.GeomInput.g4.Value = 24
model.GeomInput.g5.Value = 25
model.GeomInput.g6.Value = 26
model.GeomInput.g7.Value = 27
model.GeomInput.g8.Value = 19
model.GeomInput.g9.Value = 20

model.Geom.domain.Lower.X = 0.0
model.Geom.domain.Lower.Y = 0.0
model.Geom.domain.Lower.Z = 0.0

model.Geom.domain.Upper.X = 330000.0
model.Geom.domain.Upper.Y = 200000.0
model.Geom.domain.Upper.Z = 200.0

#First set the name for your `Domain` and setup the patches for this domain
model.Domain.GeomName = "domain"
model.Geom.domain.Patches = "x_lower x_upper y_lower y_upper z_lower z_upper"

#3.3----层数设置
model.Solver.Nonlinear.VariableDz = True
model.dzScale.GeomNames = "domain"
model.dzScale.Type = "nzList"
model.dzScale.nzListNumber = 10

model.Cell._0.dzScale.Value = 4.90
model.Cell._1.dzScale.Value = 2.50
model.Cell._2.dzScale.Value = 1.50
model.Cell._3.dzScale.Value = 1.00
model.Cell._4.dzScale.Value = 0.05
model.Cell._5.dzScale.Value = 0.02
model.Cell._6.dzScale.Value = 0.0150
model.Cell._7.dzScale.Value = 0.0075
model.Cell._8.dzScale.Value = 0.0050
model.Cell._9.dzScale.Value = 0.0025

model.Solver.Nonlinear.FlowBarrierZ = True
model.FBz.Type = "PFBFile"
model.Geom.domain.FBz.FileName = "DTB.pfb"

#3.4----地质单元设置
model.TopoSlopesX.Type = "PFBFile"
model.TopoSlopesX.GeomNames = "domain"
model.TopoSlopesX.FileName = "slopex.pfb"

model.TopoSlopesY.Type = "PFBFile"
model.TopoSlopesY.GeomNames = "domain"
model.TopoSlopesY.FileName = "slopey.pfb"

model.Mannings.Type = "PFBFile"
model.Mannings.GeomNames = "domain"
model.Mannings.FileName = "mannings.pfb"

#4.1----渗透率
model.Geom.Perm.Names = "domain s1 s2 s3 s4 s5 s6 s7 s8 s9 g1 g2 g3 g4 g5 g6 g7 g8 g9"

model.Geom.domain.Perm.Type = "Constant"
model.Geom.domain.Perm.Value = 0.2

model.Geom.s1.Perm.Type = "Constant"
model.Geom.s1.Perm.Value = 0.269022595

model.Geom.s2.Perm.Type = "Constant"
model.Geom.s2.Perm.Value = 0.043630356

model.Geom.s3.Perm.Type = "Constant"
model.Geom.s3.Perm.Value = 0.015841225

model.Geom.s4.Perm.Type = "Constant"
model.Geom.s4.Perm.Value = 0.007582087

model.Geom.s5.Perm.Type = "Constant"
model.Geom.s5.Perm.Value = 0.01818816

model.Geom.s6.Perm.Type = "Constant"
model.Geom.s6.Perm.Value = 0.005009435

model.Geom.s7.Perm.Type = "Constant"
model.Geom.s7.Perm.Value = 0.005492736

model.Geom.s8.Perm.Type = "Constant"
model.Geom.s8.Perm.Value = 0.004675077

model.Geom.s9.Perm.Type = "Constant"
model.Geom.s9.Perm.Value = 0.003386794

model.Geom.g1.Perm.Type = "Constant"
model.Geom.g1.Perm.Value = 0.02

model.Geom.g2.Perm.Type = "Constant"
model.Geom.g2.Perm.Value = 0.03

model.Geom.g3.Perm.Type = "Constant"
model.Geom.g3.Perm.Value = 0.04

model.Geom.g4.Perm.Type = "Constant"
model.Geom.g4.Perm.Value = 0.05

model.Geom.g5.Perm.Type = "Constant"
model.Geom.g5.Perm.Value = 0.06

model.Geom.g6.Perm.Type = "Constant"
model.Geom.g6.Perm.Value = 0.08

model.Geom.g7.Perm.Type = "Constant"
model.Geom.g7.Perm.Value = 0.2

model.Geom.g8.Perm.Type = "Constant"
model.Geom.g8.Perm.Value = 0.005

model.Geom.g9.Perm.Type = "Constant"
model.Geom.g9.Perm.Value = 0.01

#4.2----渗透率张力？
model.Perm.TensorType = "TensorByGeom"
model.Geom.Perm.TensorByGeom.Names = "domain"
model.Geom.domain.Perm.TensorValX = 1.0
model.Geom.domain.Perm.TensorValY = 1.0
model.Geom.domain.Perm.TensorValZ = 1.0

#4.3----给水度
model.SpecificStorage.Type = "Constant"
model.SpecificStorage.GeomNames = "domain"
model.Geom.domain.SpecificStorage.Value = 0.00001

#4.4----孔隙度
model.Geom.Porosity.GeomNames = "domain s1 s2 s3 s4 s5 s6 s7 s8 s9"

model.Geom.domain.Porosity.Type = "Constant"
model.Geom.domain.Porosity.Value = 0.4

model.Geom.s1.Porosity.Type = "Constant"
model.Geom.s1.Porosity.Value = 0.375

model.Geom.s2.Porosity.Type = "Constant"
model.Geom.s2.Porosity.Value = 0.39

model.Geom.s3.Porosity.Type = "Constant"
model.Geom.s3.Porosity.Value = 0.387

model.Geom.s4.Porosity.Type = "Constant"
model.Geom.s4.Porosity.Value = 0.439

model.Geom.s5.Porosity.Type = "Constant"
model.Geom.s5.Porosity.Value = 0.489

model.Geom.s6.Porosity.Type = "Constant"
model.Geom.s6.Porosity.Value = 0.399

model.Geom.s7.Porosity.Type = "Constant"
model.Geom.s7.Porosity.Value = 0.384

model.Geom.s8.Porosity.Type = "Constant"
model.Geom.s8.Porosity.Value = 0.482

model.Geom.s9.Porosity.Type = "Constant"
model.Geom.s9.Porosity.Value = 0.442

#4.5----相对渗透系数
model.Phase.RelPerm.Type = "VanGenuchten"
model.Phase.RelPerm.GeomNames = "domain s1 s2 s3 s4 s5 s6 s7 s8 s9"

model.Geom.domain.RelPerm.Alpha = 3.5
model.Geom.domain.RelPerm.N = 2.0

model.Geom.s1.RelPerm.Alpha = 3.548
model.Geom.s1.RelPerm.N = 4.162

model.Geom.s2.RelPerm.Alpha = 3.467
model.Geom.s2.RelPerm.N = 2.738

model.Geom.s3.RelPerm.Alpha = 2.692
model.Geom.s3.RelPerm.N = 2.445

model.Geom.s4.RelPerm.Alpha = 0.501
model.Geom.s4.RelPerm.N = 2.659

model.Geom.s5.RelPerm.Alpha = 0.661
model.Geom.s5.RelPerm.N = 2.659

model.Geom.s6.RelPerm.Alpha = 1.122
model.Geom.s6.RelPerm.N = 2.479

model.Geom.s7.RelPerm.Alpha = 2.089
model.Geom.s7.RelPerm.N = 2.318

model.Geom.s8.RelPerm.Alpha = 0.832
model.Geom.s8.RelPerm.N = 2.514

model.Geom.s9.RelPerm.Alpha = 1.585
model.Geom.s9.RelPerm.N = 2.413

#4.6----饱和度
model.Phase.Saturation.Type = "VanGenuchten"
model.Phase.Saturation.GeomNames = "domain s1 s2 s3 s4 s5 s6 s7 s8 s9"

model.Geom.domain.Saturation.Alpha = 3.5
model.Geom.domain.Saturation.N = 2.0
model.Geom.domain.Saturation.SRes = 0.2
model.Geom.domain.Saturation.SSat = 1.0

model.Geom.s1.Saturation.Alpha = 3.548
model.Geom.s1.Saturation.N = 4.162
model.Geom.s1.Saturation.SRes = 0.14
model.Geom.s1.Saturation.SSat = 1.0

model.Geom.s2.Saturation.Alpha = 3.467
model.Geom.s2.Saturation.N = 2.738
model.Geom.s2.Saturation.SRes = 1.26
model.Geom.s2.Saturation.SSat = 1.0

model.Geom.s3.Saturation.Alpha = 2.692
model.Geom.s3.Saturation.N = 2.445
model.Geom.s3.Saturation.SRes = 0.10
model.Geom.s3.Saturation.SSat = 1.0

model.Geom.s4.Saturation.Alpha = 0.501
model.Geom.s4.Saturation.N = 2.659
model.Geom.s4.Saturation.SRes = 0.15
model.Geom.s4.Saturation.SSat = 1.0

model.Geom.s5.Saturation.Alpha = 0.661
model.Geom.s5.Saturation.N = 2.659
model.Geom.s5.Saturation.SRes = 0.10
model.Geom.s5.Saturation.SSat = 1.0

model.Geom.s6.Saturation.Alpha = 1.122
model.Geom.s6.Saturation.N = 2.479
model.Geom.s6.Saturation.SRes = 0.15
model.Geom.s6.Saturation.SSat = 1.0

model.Geom.s7.Saturation.Alpha = 2.089
model.Geom.s7.Saturation.N = 2.318
model.Geom.s7.Saturation.SRes = 0.16
model.Geom.s7.Saturation.SSat = 1.0

model.Geom.s8.Saturation.Alpha = 0.832
model.Geom.s8.Saturation.N = 2.514
model.Geom.s8.Saturation.SRes = 0.19
model.Geom.s8.Saturation.SSat = 1.0

model.Geom.s9.Saturation.Alpha = 1.585
model.Geom.s9.Saturation.N = 2.413
model.Geom.s9.Saturation.SRes = 0.18
model.Geom.s9.Saturation.SSat = 1.0

#5————介质
# Phases
model.Phase.Names = "water"
model.Phase.water.Density.Type = "Constant"
model.Phase.water.Density.Value = 1.0
model.Phase.water.Viscosity.Type = "Constant"
model.Phase.water.Viscosity.Value = 1.0
model.Phase.water.Mobility.Type = "Constant"
model.Phase.water.Mobility.Value = 1.0

# Contaminants
model.Contaminants.Names = ""

# Gravity
model.Gravity = 1.0

#Wells
model.Wells.Names = ""

# Phase Sources
model.PhaseSources.water.Type = "Constant"
model.PhaseSources.water.GeomNames = "domain"
model.PhaseSources.water.Geom.domain.Value = 0.0

#6————时间
# Time units ans start and stop times
model.TimingInfo.BaseUnit = 1.0
model.TimingInfo.StartCount = 0
model.TimingInfo.StartTime = 0.0
model.TimingInfo.StopTime = 8784.0
model.TimingInfo.DumpInterval = 24.0
model.TimeStep.Type = "Constant"
model.TimeStep.Value = 1.0

#Time cycles
model.Cycle.Names ="constant"
model.Cycle.constant.Names = "alltime"
model.Cycle.constant.alltime.Length = 1
model.Cycle.constant.Repeat = -1

#7.1————边界条件
model.BCPressure.PatchNames = "x_lower x_upper y_lower y_upper z_lower z_upper"

model.Patch.x_lower.BCPressure.Type	= "FluxConst"
model.Patch.x_lower.BCPressure.Cycle = "constant"
model.Patch.x_lower.BCPressure.alltime.Value = 0.0

model.Patch.y_lower.BCPressure.Type	= "FluxConst"
model.Patch.y_lower.BCPressure.Cycle = "constant"
model.Patch.y_lower.BCPressure.alltime.Value = 0.0

model.Patch.x_upper.BCPressure.Type	= "FluxConst"
model.Patch.x_upper.BCPressure.Cycle = "constant"
model.Patch.x_upper.BCPressure.alltime.Value = 0.0

model.Patch.y_upper.BCPressure.Type	= "FluxConst"
model.Patch.y_upper.BCPressure.Cycle = "constant"
model.Patch.y_upper.BCPressure.alltime.Value = 0.0

model.Patch.z_lower.BCPressure.Type	= "FluxConst"
model.Patch.z_lower.BCPressure.Cycle = "constant"
model.Patch.z_lower.BCPressure.alltime.Value = 0.0

#model.Patch.z_upper.BCPressure.Type = "SeepageFace"
model.Patch.z_upper.BCPressure.Type	= "OverlandKinematic"
model.Patch.z_upper.BCPressure.Cycle = "constant"
model.Patch.z_upper.BCPressure.alltime.Value = 0.0
model.Solver.OverlandKinematic.Epsilon = 1E-7
model.Solver.TerrainFollowingGrid.SlopeUpwindFormulation = "Upwind"

model.Solver.ResetSurfacePressure = True
model.Solver.ResetSurfacePressure.ThresholdPressure = 2.0
model.Solver.ResetSurfacePressure.ResetPressure = 0.0
#7.2————初始条件
# Starting from a constant head values
#model.ICPressure.Type = "HydroStaticPatch"
#model.ICPressure.GeomNames = "domain"
#model.Geom.domain.ICPressure.Value = 0.0
#model.Geom.domain.ICPressure.RefGeom = "domain"
#model.Geom.domain.ICPressure.RefPatch = "z_lower"

#Starting from a previous simulation output
model.ICPressure.Type = "PFBFile"
model.ICPressure.GeomNames = "domain"
model.Geom.domain.ICPressure.RefPatch = "z_upper"
model.Geom.domain.ICPressure.FileName = "press.init.pfb"

#8.0————CLM设置
model.Solver.LSM = "CLM"
model.Solver.CLM.IstepStart = 1
model.Solver.CLM.CLMDumpInterval = 24

model.Solver.CLM.MetForcing = "3D"
model.Solver.CLM.MetFileName = "mao"
model.Solver.CLM.MetFilePath = "/XYFS01/HDD_POOL/bnu_xfyang/bnu_xfyangxy_1/ljx/2_spinup/2004_data/pfb_2004"
model.Solver.CLM.MetFileNT = 24
model.Solver.CLM.ForceVegetation = True
model.Solver.CLM.ReuseCount = 1

model.Solver.CLM.EvapBeta = "Linear"
model.Solver.CLM.VegWaterStress = "Saturation"
model.Solver.CLM.ResSat = 0.10
model.Solver.CLM.WiltingPoint = 0.12
model.Solver.CLM.FieldCapacity = 0.98
model.Solver.CLM.IrrigationType = "none"
model.Solver.CLM.RZWaterStress = 1
model.Solver.CLM.RootZoneNZ = 5
model.Solver.CLM.SoiLayer = 6
# outputs
model.Solver.CLM.CLMFileDir = "clm_output/"
model.Solver.CLM.Print1dOut = False
model.Solver.CLM.BinaryOutDir = False

#Writing CLM restart:
model.Solver.CLM.DailyRST = True
#model.Solver.CLM.WriteLastRST = True

#8.1————求解器：outputs
model.Solver.PrintSubsurfData = False
model.Solver.PrintPressure = True
model.Solver.PrintSaturation = True
model.Solver.PrintMask = False
model.Solver.PrintOverlandSum = False
model.Solver.PrintEvapTrans = True
model.Solver.PrintMask = True
model.Solver.PrintSpecificStorage = False

model.Solver.WriteCLMBinary = False
model.Solver.PrintCLM = True
model.Solver.CLM.SingleFile = False
model.Solver.WriteSiloSpecificStorage = False
model.Solver.WriteSiloMannings = True
model.Solver.WriteSiloMask = False
model.Solver.WriteSiloSlopes = False
model.Solver.WriteSiloSubsurfData = False
model.Solver.WriteSiloPressure = False
model.Solver.WriteSiloSaturation = False
model.Solver.WriteSiloEvapTrans = False
model.Solver.WriteSiloEvapTransSum = False
model.Solver.WriteSiloOverlandSum = False
model.Solver.WriteSiloCLM = False

#8.2————求解器：类型参数
# Solver types
model.Solver = "Richards"
model.Solver.TerrainFollowingGrid = True
model.Solver.Linear.Preconditioner = "PFMG"
#model.Solver.Linear.Preconditioner.PCMatrixType = "FullJacobian"

# Exact solution
model.KnownSolution = "NoKnownSolution"

# Solver settings
model.Solver.MaxIter = 100000
model.Solver.Drop = 1e-20
model.Solver.AbsTol = 1e-8

model.Solver.MaxConvergenceFailures = 8
model.Solver.Nonlinear.MaxIter = 100
model.Solver.Nonlinear.ResidualTol = 1e-5
model.Solver.Nonlinear.EtaChoice =  "EtaConstant"
model.Solver.Nonlinear.EtaValue = 0.001
model.Solver.Nonlinear.UseJacobian = True
model.Solver.Nonlinear.DerivativeEpsilon = 1e-16
model.Solver.Nonlinear.StepTol = 1e-15
model.Solver.Nonlinear.Globalization = "LineSearch"

model.Solver.Linear.KrylovDimension = 70
model.Solver.Linear.MaxRestarts = 2

#9————文件分配→ 模型配置保存 → 运行 → 结果访问
# Create a ParFlow Run object
#model = Run(runname, __file__)

# -------------- 文件分配 --------------
# 分发 2D 输入文件（坡度等）
model.ComputationalGrid.NZ = 1
model.dist("slopex.pfb")
model.dist("slopey.pfb")
model.dist("mannings.pfb")

# 恢复 NZ 为实际的 3D 值，分发 3D 输入文件
model.ComputationalGrid.NZ = 10
model.dist("IndicatorFile.pfb")
model.dist("DTB.pfb")
#model.dist("press.init.pfb")

# -------------- 写入配置文件 --------------
# 写入 pfidb、yaml 和 json 配置文件
model.write()
model.write(file_format='pfidb')
model.write(file_format='yaml')
model.write(file_format='json')

# -------------- 运行模型 --------------
model.run()
print("ParFlow Run Complete")

# -------------- 回到上级目录 --------------
os.chdir("..")
print(" - complete")