from trianglezslice import TriZSlice
import re

# load the stl files into trianglebarmeshes
transmaps = { "unit":lambda t: t, "swapyz": lambda t: (t[0], -t[2], t[1]) }

def pngname(optionoutputfile, i, z):
    if re.search("%.*?d(?i)", optionoutputfile):
        return optionoutputfile % i
    if re.search("%.*?f(?i)", optionoutputfile):
        return optionoutputfile % z
    return optionoutputfile

def stl2png(stlfile, nlayers, image_width, image_height, outfiles):
    tzs = TriZSlice(True)
    tzs.LoadSTLfile(stlfile, transmaps["unit"])
    
    extra = "5%"
    tzs.SetExtents(extra)
    tzs.BuildPixelGridStructures(image_width, image_height)
    
    for i in range(nlayers):
        z = tzs.zlo + (tzs.zhi - tzs.zlo)*(i + 0.5)/nlayers
        tzs.SliceToPNG(z, pngname(outfiles, i, z))   
    return
          