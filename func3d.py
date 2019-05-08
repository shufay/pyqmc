import numpy as np
""" 
Collection of 3d functions
"""

class GaussianFunction:
    def __init__(self,exponent):
        self.parameters={}
        self.parameters['exponent']=exponent

    def value(self,x): 
        """Return the value of the function. 
        x should be a (nconfig,3) vector """
        r2=np.sum(x**2,axis=1)
        return np.exp(-self.parameters['exponent']*r2)
        
    def gradient(self,x):
        """ return gradient of the function """
        v=self.value(x)
        return -2*self.parameters['exponent']*x*v[:,np.newaxis]

    def laplacian(self,x):
        """ laplacian """
        v=self.value(x)
        alpha=self.parameters['exponent']
        return (4*alpha*alpha*x*x-2*alpha)*v[:,np.newaxis]


    def pgradient(self,x):
        """ parameter gradient """
        
class PadeFunction:
    """
    a_k(r) = (alpha_k*r/(1+alpha_k*r))^2
    alpha_k = alpha/2^k, k starting at 0
    """
    def __init__(self, alphak):
        self.parameters={}
        self.parameters['alphak'] = alphak

    def value(self, rvec):
        """
        Parameters:
          rvec: nconf x ... x 3 (number of inner dimensions doesn't matter)
        Return:
          func: same dimensions as rvec, but the last one removed 
        """
        r = np.linalg.norm(rvec, axis=-1)
        a = self.parameters['alphak']* r
        return (a/(1+a))**2

    def gradient(self, rvec):
        """
        Parameters:
          rvec: nconf x ... x 3, displacement between particles
            For example, nconf x n_elec_pairs x 3, where n_elec_pairs could be all pairs of electrons or just the pairs that include electron e for the purpose of updating one electron.
            Or it could be nconf x nelec x natom x 3 for electron-ion displacements
        Return:
          grad: same dimensions as rvec
        """
        r = np.linalg.norm(rvec, axis=-1, keepdims=True)
        a = self.parameters['alphak']* r
        grad = 2* self.parameters['alphak']**2/(1+a)**3 *rvec
        return grad
        
    def laplacian(self, rvec):
        """
        Parameters:
          rvec: nconf x ... x 3
        Return:
          lap: same dimensions as rvec, d2/dx2, d2/dy2, d2/dz2 separately
        """
        r = np.linalg.norm(rvec, axis=-1, keepdims=True)
        a = self.parameters['alphak']* r
        #lap = 6*self.parameters['alphak']**2 * (1+a)**(-4) #scalar formula
        lap = 2*self.parameters['alphak']**2 * (1+a)**(-3) \
              *(1 - 3*a/(1+a)*(rvec/r)**2)
        return lap

    def pgradient(self, rvec):
        """ Return gradient of value with respect to parameter alphak
        Parameters:
          rvec: nconf x ... x 3
        Return:
          akderiv: same dimensions as rvec, but the last one removed 
        
        """
        r = np.linalg.norm(rvec, axis=-1)
        a = self.parameters['alphak']* r
        akderiv = 2*a/(1+a)**3 * r
        return akderiv

def test_func3d_gradient(bf, delta=1e-5):
    rvec = np.random.randn(10,3)
    grad = bf.gradient(rvec)
    numeric = np.zeros(rvec.shape)
    for d in range(3):
      pos = rvec.copy()
      pos[:,d] += delta
      plusval = bf.value(pos)
      pos[:,d] -= 2*delta
      minuval = bf.value(pos)
      numeric[:,d] = (plusval - minuval)/(2*delta)
    maxerror = np.amax(np.abs(grad-numeric))
    normerror = np.linalg.norm(grad-numeric)
    return (maxerror,normerror)

def test_func3d_laplacian(bf, delta=1e-5):
    rvec = np.random.randn(10,3)
    lap = bf.laplacian(rvec)
    numeric = np.zeros(rvec.shape)
    for d in range(3):
      pos = rvec.copy()
      pos[:,d] += delta
      plusval = bf.gradient(pos)[:,d]
      pos[:,d] -= 2*delta
      minuval = bf.gradient(pos)[:,d]
      numeric[:,d] = (plusval - minuval)/(2*delta)
    maxerror = np.amax(np.abs(lap-numeric))
    normerror = np.linalg.norm(lap-numeric)
    return (maxerror,normerror)

def test(): 
    test_functions = {'Pade':PadeFunction(0.2), 'Gaussian':GaussianFunction(0.4)}
    for name, func in test_functions.items():
        for delta in [1e-3,1e-4,1e-5,1e-6,1e-7]:
            print(name, 'delta', delta, "Testing gradient", test_func3d_gradient(func,delta=delta))
            print(name, 'delta', delta, "Testing laplacian", test_func3d_laplacian(func,delta=delta))
    
if __name__=="__main__":
    test()