import numpy as np

def is_3D(twix):
    return twix[-1]['hdr']['Config']['Is3D']=='true'

def get_protocol_name(twix):
    return twix[-1]['hdr']['Config']['ProtocolName']

def get_flip_angle(twix):
    return twix[-1]['hdr']['Dicom']['adFlipAngleDegree'] # degree

def get_scan_time(twix, total=True):
    if total:
        return twix[-1]['hdr']['Meas']['lTotalScanTimeSec'] #s
    else:
        return twix[-1]['hdr']['Meas']['lScanTimeSec'] #s

def get_base_res(twix):
    return int(twix[-1].hdr.Dicom.lBaseResolution)

def get_phase_res(twix):
    def closest_multiple(n,f):
        inf = f*(n//f)
        sup = inf+f
        if n-inf<sup-n:
            return inf
        else:
            return sup
    phase_res = twix[-1].hdr.Meas.dPhaseResolution*get_base_res(twix)
    acc_factor = twix[-1].hdr.Meas.dTotalAccelFact
    return int(closest_multiple(phase_res, acc_factor)) # phase res is a multiple of the acc factor

def get_slice_res(twix):
    slice_res = twix[-1].image.NPar if is_3D(twix) else twix[-1].image.NSli
    return int(slice_res)

def get_matrix(twix):
    return np.array([get_base_res(twix), get_phase_res(twix), get_slice_res(twix)])

def get_FOV(twix):
    readout_FOV = twix[-1].hdr.Dicom.dReadoutFOV
    phase_FOV = twix[-1].hdr.Dicom.dPhaseFOV
    slice_FOV = twix[-1].hdr.Dicom.dThickness*int(twix[-1].image.NSli)
    return np.array([readout_FOV, phase_FOV, slice_FOV])

def get_voxel_size(twix):
    return get_FOV(twix)/get_matrix(twix)