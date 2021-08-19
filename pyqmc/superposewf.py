import numpy as np
from pyqmc.multiplywf import Parameters

class SuperposeWF:
    """
    A general representation of a wavefunction as a superposition of multiple wfs
    """

    def __init__(self, coeffs, wf_components):
        self.coeffs = coeffs 
        self.wf_components = wf_components
        self.parameters = Parameters([wf.parameters for wf in wf_components])
        self.iscomplex = bool(sum(wf.iscomplex for wf in wf_components)+sum([isinstance(c, complex)*1 for c in coeffs]))
        self.dtype = complex if self.iscomplex else float

    def recompute(self, configs):
        """
        Recompute the quantity :math:`ln(|\psi(R)|)` and the phase/sign of the wave function.
        """
        wf_vals = np.array([wf.recompute(configs) for wf in self.wf_components])
        ref = np.amax(wf_vals[:,1,:]).real
        wf_val = np.einsum('i,ij,ij->j',self.coeffs,wf_vals[:,0,:],np.exp(wf_vals[:,1,:] - ref))
        wf_sign = wf_val / np.abs(wf_val)
        wf_val = np.log(np.abs(wf_val)) + ref
        return wf_sign, wf_val

    def updateinternals(self, e, epos, mask=None):
        """
        Update the electron e position to epos, for each wf component in self.wf_components 
        """
        for wf in self.wf_components:
            wf.updateinternals(e, epos, mask=mask)

    def value(self):
        """
        Compute the quantity :math:`ln(|\psi(R)|)` and the phase/sign of the wave function.
        
        Returns:
          phase/sign of the wave function psi(R), the value ln|psi(R)|
        """
        wf_vals = np.array([wf.value() for wf in self.wf_components])
        ref = np.amax(wf_vals[:,1,:]).real
        wf_val = np.einsum('i,ij,ij->j',self.coeffs,wf_vals[:,0,:], np.exp(wf_vals[:,1,:]-ref))
        wf_sign = wf_val/np.abs(wf_val)
        wf_val = np.log(np.abs(wf_val))+ref
        return wf_sign, wf_val

    def ratio_current_config(self, mask=None):
        """
        Compute the ratio :math:`c_i \psi_i(R)/\psi(R)` at current configuration R,
        where :math:`\psi_i` is the ith component.

        Args: 
          mask: a mask (optional) on configuration
        Returns:
          ratio c*psi_i(R)/psi(R)
        """
        wf_vals = np.array([wf.value() for wf in self.wf_components])
        ref = np.amax(wf_vals[:,1,:]).real
        wf_val = np.einsum('i,ij,ij->j',self.coeffs,wf_vals[:,0,:],np.exp(wf_vals[:,1,:] - ref))
        wf_sign = wf_val / np.abs(wf_val)
        wf_val = np.log(np.abs(wf_val)) + ref
        ratio = np.einsum('i,i...j,i...j->i...j',self.coeffs, wf_vals[:,0,mask]/wf_sign[mask], np.exp(wf_vals[:,1,mask]-wf_val[mask]))
        if ratio.shape[1] == 1: ratio = np.squeeze(ratio)
        return ratio

    def ratio(self, e, epos, mask=None):
        """
        Compute the ratio :math:`c_i \psi_i(R')/\psi(R')` at configuration R',
        where electron e has been displaced to epos.

        Args:
          e: which electron to move
          epos: move electron e to epos
          mask: a mask (optional) on configuration
        Returns: 
          ratio c*psi_i(R')/psi(R')
        """
        wf_vals = np.array([wf.value() for wf in self.wf_components])
        ref = np.amax(wf_vals[:,1,:]).real
        wf_val = np.einsum('i,ij,ij->j',self.coeffs,wf_vals[:,0,:],np.exp(wf_vals[:,1,:] - ref))
        wf_sign = wf_val / np.abs(wf_val)
        wf_val = np.log(np.abs(wf_val)) + ref
        testvals = [wf.testvalue(e, epos, mask) for wf in self.wf_components]
        ratio = np.einsum('i,i...j,i...j,ij->i...j',self.coeffs, wf_vals[:,0,mask]/wf_sign, np.exp(wf_vals[:,1,mask]-wf_val),testvals/self.testvalue(e, epos, mask))
        if ratio.shape[1] == 1: ratio = np.squeeze(ratio)
        return ratio

    def gradient(self, e, epos):
        """
        Compute the gradient of the log wave function, which is the quantity :math:`\nabla_e \psi/\psi|_{R'}`.  
        """
        grads_components = np.array([wf.gradient(e, epos) for wf in self.wf_components])
        return np.einsum('ijk,ik->jk',grads_components, self.ratio(e, epos))

    def testvalue(self, e, epos, mask=None):
        """
        Compute the ratio :math:`\psi(R')/\psi(R)`, where R' is the configuration when electron e's position is replaced by epos.
        """
        testvalue_components = np.array([wf.testvalue(e, epos, mask=mask) for wf in self.wf_components])
        return np.einsum('ij...,ij->j...',testvalue_components, self.ratio_current_config(mask))
       
    def testvalue_many(self, e, epos, mask=None):
        """
        Compute the ratio :math:`\psi(R')/\psi(R)`, where R' is the configuration when electron e's position is replaced by epos for each electron.
        """
        testvalue_components = np.array([wf.testvalue_many(e, epos, mask=mask) for wf in self.wf_components])
        return np.einsum('ijk,ij->jk',testvalue_components, self.ratio_current_config(mask))

    def gradient_value(self, e, epos):
        """
        Compute the gradient of the log wave function, and the ratio psi(R')/psi(R).
        """
        grad_vals = [wf.gradient_value(e, epos) for wf in self.wf_components]
        grads, vals = list(zip(*grad_vals))
        ratio = self.ratio(e, epos)
        grad = np.einsum('ijk,ik->jk',grads, ratio)
        val = np.einsum('ij,ij->j', vals, self.ratio_current_config())
        return grad, val

    def gradient_laplacian(self, e, epos):
        """
        Compute the gradient of the log wave function, and the quantity :math:`\nabla^2 \psi/\psi|_{R'}`
        """
        grad_laps = [wf.gradient_laplacian(e, epos) for wf in self.wf_components]
        grads, laps = list(zip(*grad_laps))
        ratio = self.ratio(e, epos)
        return np.einsum('ijk,ik->jk', grads, ratio), np.einsum('ij,ij->j', laps, ratio)
        

    def laplacian(self, e, epos):
        """
        Compute the laplacian of psi over psi
        """
        laps = [wf.laplacian(e, epos) for wf in self.wf_components]
        return np.einsum('ij,ij->j', laps, self.ratio(e, epos))

    def pgradient(self):
        """
        Compute the gradient of the parameters
        """
        ratio = self.ratio_current_config()
        pgrad = []
        for iwf, wf in enumerate(self.wf_components):
            pgrad_tmp = wf.pgradient()
            for k in wf.pgradient().keys():
                pgrad_tmp[k] = np.einsum('i...,i->i...', pgrad_tmp[k], ratio[iwf,:])
            pgrad.append(pgrad_tmp)
        return Parameters(pgrad)