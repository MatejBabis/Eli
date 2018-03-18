# Copyright (c) 2012, GPy authors (see AUTHORS.txt).
# Licensed under the BSD 3-clause license (see LICENSE.txt)

import numpy as np
from .kern import Kern
from ...util.linalg import tdot
from ...core.parameterization import Param
from paramz.transformations import Logexp
from paramz.caching import Cache_this
from .psi_comp import PSICOMP_Linear
from ...util.linalg import tdot
from ... import util


class PjkRbf(Kern):
    """
    PjkRbf kernel
   
    """
    _support_GPU = False
    def __init__(self, input_dim, variance=None, lengthscale=None, active_dims=None, name='pjkrbf'):      
        super(PjkRbf, self).__init__(input_dim, active_dims, name)
        
        self.lengthscale = Param('lengthscale', lengthscale, Logexp())
        self.variance    = Param('variance', variance, Logexp())
        assert self.variance.size==1
        assert self.lengthscale.size==1
        self.link_parameters(self.variance, self.lengthscale)
        
               
    def K(self, X, X2=None):
       
        indU = range(0,X.shape[1]/2)
        indV = range(X.shape[1]/2,X.shape[1])
        
        
     
        #print "Subpart of X is: "        
        #print X[:,indU]
        if X2 is not None:
            Kuuxz = self._RbfBase_K( X[:,indU], X2[:,indU] )
            Kvvxz = self._RbfBase_K( X[:,indV], X2[:,indV] )       
            Kuvxz = self._RbfBase_K( X[:,indU], X2[:,indV] )
            Kvuxz = self._RbfBase_K( X[:,indV], X2[:,indU] )
        else:
            Kuuxz = self._RbfBase_K( X[:,indU], None )
            Kvvxz = self._RbfBase_K( X[:,indV], None )       
            Kuvxz = self._RbfBase_K( X[:,indU], X[:,indV] )
            Kvuxz = self._RbfBase_K( X[:,indV], X[:,indU] )  
            
        Ktmp = Kuuxz + Kvvxz - Kuvxz - Kvuxz;
          
        #print "K is"
        #print Ktmp
        return Ktmp

    def Kdiag(self, X):
        indU = range(0,X.shape[1]/2)
        indV = range(X.shape[1]/2,X.shape[1])
      
        KuuFull = self._RbfBase_K( X[:,indU]);
        KvvFull = self._RbfBase_K( X[:,indV]);        
        KuvFull = self._RbfBase_K( X[:,indU], X[:,indV]);
        
        KuuDiag = np.diag(KuuFull);
        KvvDiag = np.diag(KvvFull);        
        KuvDiag = np.diag(KuvFull);
                            
        KtmpDiag = KuuDiag + KvvDiag - 2*KuvDiag; # note with teh rbf this is 0
     
        return KtmpDiag

    def _RbfBase_K(self, X, X2=None):
        r = self._scaled_dist(X, X2)
        
        K = self.variance * np.exp(-0.5 * r**2)
        return K
        
    def _RbfBase_Kdiag(self, X):
        ret = np.empty(X.shape[0])
        ret[:] = self.variance
        return ret
       
           
    def update_gradients_diag(self, dL_dKdiag, X):
        """
        Given the derivative of the objective with respect to the diagonal of
        the covariance matrix, compute the derivative wrt the parameters of
        this kernel and stor in the <parameter>.gradient field.

        See also update_gradients_full
        """
#        self.variance.gradient = np.sum(dL_dKdiag)
#        self.lengthscale.gradient = 0.

    def update_gradients_full(self, dL_dK, X, X2=None):
        """
        Given the derivative of the objective wrt the covariance matrix
        (dL_dK), compute the gradient wrt the parameters of this kernel,
        and store in the parameters object as e.g. self.variance.gradient
        """
#        self.variance.gradient = np.einsum('ij,ij,i', self.K(X, X2), dL_dK, 1./self.variance)
#
#        r = self._scaled_dist(X, X2)
#        self.lengthscale.gradient = -np.sum(dL_dr*r)/self.lengthscale

        
#    def update_gradients_full(self, dL_dK, X, X2=None):
#        [p.update_gradients_full(dL_dK, X, X2) for p in self.parts if not p.is_fixed]
#
#    def update_gradients_diag(self, dL_dK, X):
#        [p.update_gradients_diag(dL_dK, X) for p in self.parts]
#
#    
#    
#    def update_gradients_full(self, dL_dK, X, X2=None):
#        k = self.K(X,X2)*dL_dK
#        for p in self.parts:
#            p.update_gradients_full(k/p.K(X,X2),X,X2)
#
#    def update_gradients_diag(self, dL_dKdiag, X):
#        k = self.Kdiag(X)*dL_dKdiag
#        for p in self.parts:
#            p.update_gradients_diag(k/p.Kdiag(X),X)


  

    # ----------------------------------------------------------------------

    def _unscaled_dist(self, X, X2=None):
        """
        Compute the Euclidean distance between each row of X and X2, or between
        each pair of rows of X if X2 is None.
        """
        #X, = self._slice_X(X)
        if X2 is None:
            Xsq = np.sum(np.square(X),1)
            r2 = -2.*tdot(X) + (Xsq[:,None] + Xsq[None,:])
            util.diag.view(r2)[:,]= 0. # force diagnoal to be zero: sometime numerically a little negative
            r2 = np.clip(r2, 0, np.inf)
            return np.sqrt(r2)
        else:
            #X2, = self._slice_X(X2)
            X1sq = np.sum(np.square(X),1)
            X2sq = np.sum(np.square(X2),1)
            r2 = -2.*np.dot(X, X2.T) + X1sq[:,None] + X2sq[None,:]
            r2 = np.clip(r2, 0, np.inf)
            return np.sqrt(r2)

    @Cache_this(limit=5, ignore_args=())
    def _scaled_dist(self, X, X2=None):
        """
        Efficiently compute the scaled distance, r.

        r = \sqrt( \sum_{q=1}^Q (x_q - x'q)^2/l_q^2 )

        Note that if thre is only one lengthscale, l comes outside the sum. In
        this case we compute the unscaled distance first (in a separate
        function for caching) and divide by lengthscale afterwards

        """
#        if self.ARD:
#            if X2 is not None:
#                X2 = X2 / self.lengthscale
#            return self._unscaled_dist(X/self.lengthscale, X2)
#        else:
        return self._unscaled_dist(X, X2)/self.lengthscale

   


    def _inv_dist(self, X, X2=None):
        """
        Compute the elementwise inverse of the distance matrix, expecpt on the
        diagonal, where we return zero (the distance on the diagonal is zero).
        This term appears in derviatives.
        """
        dist = self._scaled_dist(X, X2).copy()
        return 1./np.where(dist != 0., dist, np.inf)

    def weave_lengthscale_grads(self, tmp, X, X2):
        """Use scipy.weave to compute derivatives wrt the lengthscales"""
        N,M = tmp.shape
        Q = X.shape[1]
        if hasattr(X, 'values'):X = X.values
        if hasattr(X2, 'values'):X2 = X2.values
        grads = np.zeros(self.input_dim)
        code = """
        double gradq;
        for(int q=0; q<Q; q++){
          gradq = 0;
          for(int n=0; n<N; n++){
            for(int m=0; m<M; m++){
              gradq += tmp(n,m)*(X(n,q)-X2(m,q))*(X(n,q)-X2(m,q));
            }
          }
          grads(q) = gradq;
        }
        """
        weave.inline(code, ['tmp', 'X', 'X2', 'grads', 'N', 'M', 'Q'], type_converters=weave.converters.blitz, support_code="#include <math.h>")
        return -grads/self.lengthscale**3

    def K_of_r(self, r):
        return self.variance * np.exp(-0.5 * r**2)

    def dK_dr(self, r):
        return -r*self.K_of_r(r)
                
    def gradients_X(self, dL_dK, X, X2=None):
        raise NotImplementedError

    def gradients_X_diag(self, dL_dKdiag, X):
        raise NotImplementedError
    
    @Cache_this(limit=2, force_kwargs=['which_parts'])
    def psi0(self, Z, variational_posterior):
        raise NotImplementedError
    
    @Cache_this(limit=2, force_kwargs=['which_parts'])
    def psi1(self, Z, variational_posterior):
        raise NotImplementedError

    @Cache_this(limit=2, force_kwargs=['which_parts'])
    def psi2(self, Z, variational_posterior):
        raise NotImplementedError

    def update_gradients_expectations(self, dL_dpsi0, dL_dpsi1, dL_dpsi2, Z, variational_posterior):
        raise NotImplementedError

    def gradients_Z_expectations(self, dL_psi0, dL_dpsi1, dL_dpsi2, Z, variational_posterior):
        raise NotImplementedError

    def gradients_qX_expectations(self, dL_dpsi0, dL_dpsi1, dL_dpsi2, Z, variational_posterior):
        raise NotImplementedError

    def add(self, other):
        raise NotImplementedError

    def input_sensitivity(self, summarize=True):
        raise NotImplementedError
