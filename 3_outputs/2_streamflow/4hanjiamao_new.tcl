#-----------------------------------------------------------------------------
#Calculate Flow using Mannings equation on USGS stations
## units = m3/s
#-----------------------------------------------------------------------------

# Import the ParFlow TCL package
lappend   auto_path $env(PARFLOW_DIR)/bin
package   require parflow
namespace import Parflow::*

pfset     FileVersion    4

pfset Process.Topology.P 11
pfset Process.Topology.Q 5
pfset Process.Topology.R 1

#-----------------------------------------------------------------------------
# Computational Grid
#-----------------------------------------------------------------------------
pfset ComputationalGrid.Lower.X           0.0
pfset ComputationalGrid.Lower.Y           0.0
pfset ComputationalGrid.Lower.Z           0.0

pfset ComputationalGrid.NX                330
pfset ComputationalGrid.NY                200
pfset ComputationalGrid.NZ                10

pfset ComputationalGrid.DX                1000.0
pfset ComputationalGrid.DY                1000.0
pfset ComputationalGrid.DZ                1.0

set dx                                    1000.0
set dy                                    1000.0
set dz                                    1.0

#-----------------------------------------------------------------------------
# Runname Directory and timing
#-----------------------------------------------------------------------------
set timesteps  8760
set runname        "mao"
cd "./run_1"

# Read in all of the general files
set mask                [pfload $runname.out.mask.pfb]
set top                 [pfcomputetop $mask]
set sx                  [pfload slopex.pfb]
set sy                  [pfload slopey.pfb]
set manning             [pfload mannings.pfb]

# Create output directory if it doesn't exist
set output_dir "../2_q_outputs/4hanjiamao"
if {![file exists $output_dir]} {
    file mkdir $output_dir
    puts stdout "Created output directory: $output_dir"
}

# Define the points to calculate (X, Y coordinates)
# 根据4hanjiamao站点的情况定义坐标点
set points [list \
    [list 187 74] \
]

# 预计算每个点的坡度并打开所有输出文件
puts stdout "Pre-calculating slopes and opening output files..."
array unset slope
array unset output

foreach point $points {
    set Xloca [lindex $point 0]
    set Yloca [lindex $point 1]
    
    # 计算并存储坡度
    set sx1 [pfgetelt $sx $Xloca $Yloca 0]
    set sy1 [pfgetelt $sy $Xloca $Yloca 0]
    set S [expr ($sx1**2+$sy1**2)**0.5]
    set slope($Xloca,$Yloca) $S
    puts stdout "Slope at $Xloca $Yloca = $S"
    
    # 打开输出文件
    set filename "$output_dir/${Xloca}_${Yloca}.txt"
    set output($Xloca,$Yloca) [open $filename w]
    puts $output($Xloca,$Yloca) "Time\t  Pressure(m)\t  Flow(cms)\t"
}

# 循环处理每个时间步 - 一次性读取所有站点的值
puts stdout "Starting time series processing..."
for {set ii 0} {$ii <= $timesteps} {incr ii} {
    
    # 一次性读取压力文件
    set press [pfload [format $runname.out.press.%05d.pfb $ii]]
    
    # 一次性读取饱和度文件（如果需要）
    set satin [format $runname.out.satur.%05d.pfb $ii]
    set satur [pfload $satin]
    
    # 打印当前处理的文件信息（每100个时间步打印一次）
    if {$ii % 100 == 0} {
        puts stdout "Processing time step $ii of $timesteps"
        puts stdout "  Reading: $runname.out.press.[format %05d $ii].pfb"
    }
    
    # 同时处理所有点
    foreach point $points {
        set Xloca [lindex $point 0]
        set Yloca [lindex $point 1]
        
        # 获取该点的压力值（第9层）
        set P [pfgetelt $press $Xloca $Yloca 9]
        
        # 获取预计算的坡度
        set S $slope($Xloca,$Yloca)
        
        # Calculate the flow
        if {$P >= 0} {
            # 每1000个时间步打印一次压力值
            if {$ii % 1000 == 0} {
                puts stdout "Top Pressure = $P at time $ii for point ($Xloca, $Yloca)"
            }
            set QT [expr ($dx/9.72e-6)*($S**0.5)*($P**(5./3.))/3600]
        } else {
            set P 0
            set QT 0
        }
        
        # 写入对应的输出文件
        puts $output($Xloca,$Yloca) "$ii\t $P\t $QT\t"
    }
    
    # Clean up - 每个时间步只删除一次
    pfdelete $press
    unset press
    pfdelete $satur
    unset satur
}

# 关闭所有输出文件
puts stdout "Closing output files..."
foreach point $points {
    set Xloca [lindex $point 0]
    set Yloca [lindex $point 1]
    close $output($Xloca,$Yloca)
    puts stdout "Finished processing point ($Xloca, $Yloca)"
}

cd "../"
puts stdout "All processing complete!"