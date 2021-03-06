import math
import numpy as np
import sklearn
import time
import scipy.stats as sps
import pandas as pd
import datetime
import pickle
import csv

from scipy import linalg


def Covariance_NW(data_cov,lambd,delay=2):
    # return Newey-West estimate of covariance
    # no modification for time period
    #  i.e. if the input data is daily, the output is daily
    
    Tn = data_cov.shape[0]
    Fn = data_cov.shape[1]
    
    # exponentially decay weights
    w = np.array([lambd**n for n in range(Tn)][::-1])
    w = w/w.sum()
    
    # wighted average of factors
    f_mean_w = np.average(data_cov,axis=0,weights=w)
    
    
    # variance: factors - wighted average of factors; 
    # Combining i_th and j_th to get the covariance
    f_cov_raw = np.array([ data_cov[:,i] - f_mean_w[i] for i in range(Fn) ])
    
    
    # Calculate the cov matrix
    F_raw = 
    F_raw = np.zeros((Fn,Fn))
    for i in range(Fn):
        for j in range(Fn):
            cov_ij = np.sum( f_cov_raw[i] * f_cov_raw[j] * w ) 
            F_raw[i,j] = cov_ij

    # NW modification for autocorrelation
    for d in range(1,delay+1):
        cov_nw_i = np.zeros((Fn,Fn))
        for i in range(Fn):
            for j in range(Fn):
                cov_ij = np.sum( f_cov_raw[i][:-d] * f_cov_raw[j][d:] * w[d:] ) / np.sum(w[d:])
                cov_nw_i[i,j] = cov_ij
        
        F_NW += (1-d/(delay+1.)) * (cov_nw_i + cov_nw_i.T) 
    
    return F_NW




def NW_adjusted(data, tau=90,length=100, n_start=100, n_forward=21, NW=True):
    '''
    Input:
    data        The pandas dataframe of factor return with the last column being dates
    tau         Half life
    length      How many frames are used to calculate the covariance matrix
                The length must be greater than Fn (the No. of factors)
    n_start     'n_start-length' to 'n_start' frames are used to get the covariance
    n_forward   The period ahead to calculate bias B; standard deviation of r_ahead / risk_predicted
    
    
    n_start-length           n_start               n_start+n_forward 
          |---------------------|-------------------------|
                   NW_cov                  Bias
    
    Output:
    F_NW       
    
    Other parameters:
    Tn          No. of frames
    Fn          No. of factors
    
    '''
    
    if n_start<length:
        print('ERROR: n_start should be greater than length')
        return
    elif n_start+n_forward>=data.shape[0]:
        print('ERROR: n_start + n_forward should be greater than No. of total frames')
        return
    
    
    data_cov = data.iloc[n_start-length:n_start,:].as_matrix()
    
    lambd = 0.5**(1./tau)
    
    # calculate Newey-West covariance
    if NW:
        F_NW = n_forward*Covariance_NW(data_cov,lambd)
    else:
        F_NW = n_forward*np.cov(data_cov.T)
    
    # decomp of NW covariance 
    s, U = linalg.eigh(F_NW)
    
    r = (data.iloc[n_start:n_start+n_forward,:]+1).cumprod().iloc[-1,:]-1
    R_eigen   = np.dot(U.T,r)
    Var_eigen = s
    
    if not np.allclose(F_NW,  U @ np.diag(s) @ U.T ):
        print('ERROR in eigh')
        return
    
    return data_cov, U, F_NW, R_eigen, np.sqrt(Var_eigen)


def Eigen_adjusted(F_NW,U,Std_i,length=252,N_mc=1000):
    
    for i in range(N_mc):
        
        if i%200==0:print(i)
        
        r_mc = np.array([np.random.normal(0, std_, length) for std_ in Std_i])
        r_mc = np.dot(U,r_mc)
        
        
        F_mc = np.cov(r_mc)
        s, U_mc = linalg.eigh(F_mc)
        q = (U_mc.T@F_NW)@(U_mc)
        
        
        if i==0:
            stat = np.diagonal(q)/s
        else:
            stat+= np.diagonal(q)/s
    
    stat = np.sqrt(stat/N_mc)
    
    return stat
