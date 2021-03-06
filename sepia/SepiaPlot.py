#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

sns.set(style="ticks")

def theta_pairs(samples_dict,design_names=None,native=False,lims=None,theta_ref=None,save=None):
    """
    Create pairs plot of sampled thetas.

    :param dict samples_dict: samples from model.get_samples()
    :param list/NoneType design_names: list of string names for thetas, optional (None will use default names)
    :param bool native: put theta on native scale? (note: you likely want to pass lims in this case)
    :param list lims: list of tuples, limits for each theta value for plotting; defaults to [0, 1] if native=False
    :param list theta_ref: scalar reference values to plot as vlines on distplots and as red dots on bivariate plots
    :param str save: file name to save plot
    :returns: matplotlib figure
    """
    if 'theta' not in samples_dict.keys():
        print('No thetas to plot')
        return
    if native is False:
        theta = samples_dict['theta']
    else:
        theta = samples_dict['theta_native']
    n_samp, n_theta = theta.shape
    if native is False and lims is None:
        lims = [(0, 1) for i in range(n_theta)]
    if isinstance(design_names, list) and len(design_names) != n_theta:
        raise ValueError('Design names wrong length')
    if design_names is None:
        design_names = ['theta_%d' % (i+1) for i in range(n_theta)]
    thin_idx = np.linspace(0,n_samp-1,np.min([n_samp-1, 1000]),dtype=int) # thin to at most 1000 samples
    theta_df = pd.DataFrame(theta[thin_idx,:],columns=design_names) # take only 1000 samples to dataframe
    theta_df.insert(0,'idx',theta_df.index,allow_duplicates = False)
    
    if theta_df.shape[1]>2:
        g = sns.PairGrid(theta_df.loc[:, theta_df.columns != 'idx'], diag_sharey=False);
        g.map_upper(sns.scatterplot, palette = 'coolwarm', hue=theta_df['idx'], legend=False);
        g.map_lower(sns.kdeplot, cmap="viridis", shade=True, shade_lowest=False);
        g.map_diag(sns.distplot, hist=True);
        if lims is not None:
            # Undo sharing of axes
            for i in range(n_theta):
                [g.diag_axes[i].get_shared_x_axes().remove(axis) for axis in g.axes.ravel()];
                for j in range(n_theta):
                    [g.axes[i, j].get_shared_x_axes().remove(axis) for axis in g.axes.ravel()];
                    [g.axes[i, j].get_shared_y_axes().remove(axis) for axis in g.axes.ravel()];
                    [g.axes[i, j].get_shared_x_axes().remove(axis) for axis in g.diag_axes.ravel()];
                    [g.axes[i, j].get_shared_y_axes().remove(axis) for axis in g.diag_axes.ravel()];
            # Set limits
            for i in range(n_theta):
                for j in range(n_theta):
                    if i == j:
                        g.diag_axes[i].set_xlim(xmin=lims[i][0], xmax=lims[i][1]);
                        g.axes[i, i].set_xlim(xmin=lims[i][0], xmax=lims[i][1]);
                    else:
                        g.axes[i, j].set_xlim(xmin=lims[j][0], xmax=lims[j][1]);
                        g.axes[i, j].set_ylim(ymin=lims[i][0], ymax=lims[i][1]);
                        
        if theta_ref is not None:
            for i in range(n_theta):
                g.diag_axes[i].vlines(theta_ref[i],ymin=0,ymax=1,transform = g.diag_axes[i].get_xaxis_transform(),color='r');
                for j in range(n_theta):
                    if i>j: # Lower diag contour plots
                        g.axes[i,j].scatter(theta_ref[j], theta_ref[i], marker='o', s=5, color="red");
        if save is not None: 
            plt.tight_layout()
            plt.savefig(save,dpi=300,bbox_inches='tight')
        return g.fig
    else:
        fig,ax=plt.subplots()
        sns.distplot(theta_df.loc[:, theta_df.columns != 'idx'],hist=True,axlabel=design_names[0],ax=ax)
        if save is not None: 
            plt.tight_layout()
            plt.savefig(save,dpi=300,bbox_inches='tight')
        return fig
        
def mcmc_trace(samples_dict,theta_names=None,start=0,end=None,n_to_plot=500,by_group=True,max_print=10,save=None):
    """
    Create trace plot of MCMC samples.

    :param dict samples_dict: samples from model.get_samples()
    :param list/NoneType theta_names: list of string names for thetas, optional (None will use default names)
    :param int start: where to start plotting traces (sample index)
    :param int/NoneType end: where to end plotting traces (sample index)
    :param int n_to_plot: how many samples to show
    :param bool by_group: group params of the same name onto one axis?
    :param int max_print: maximum number of traces to plot
    :param str save: file name to save plot
    :returns: matplotlib figure
    """
    # trim samples dict
    n_samples = samples_dict['lamUz'].shape[0]
    if n_to_plot>n_samples:
        n_to_plot = n_samples
    # default end
    if end is None:
        end = n_samples-1
    # check start is valid
    if not isinstance(start,int) or start<0 :
        raise TypeError('invalid start index')
    # check end is valid
    if end is not None and (start>end or end<0 or not isinstance(end,int) or end > n_samples):
        raise TypeError('invalid end index')
    # which indices to plot  
    if (end-start) > n_to_plot:
        plot_idx = np.unique(np.linspace(start,end,n_to_plot,dtype=int))
    else:
        plot_idx = np.arange(start,end,1,dtype=int)
    
    if not by_group:
        total_plots = 0
        for i,k in enumerate(samples_dict.keys()):
            if k == 'theta_native':
                continue
            total_plots += min(samples_dict[k].shape[1],max_print)
        fig,axs = plt.subplots(total_plots,1,sharex=True,figsize=[10,1.5*total_plots])
        fig.subplots_adjust(hspace=0)
        axs_idx = 0
        for i, k in enumerate(samples_dict.keys()):
            if k == 'theta_native':
                continue
            n_theta = min(samples_dict[k].shape[1],max_print)
            if n_theta > 1:
                for j in range(n_theta):
                    sns.lineplot(x=plot_idx,y=samples_dict[k][plot_idx,j], palette="tab10", linewidth=.75, ax = axs[axs_idx])
                    if k=='theta' and theta_names is not None: axs[axs_idx].set_ylabel(theta_names[j])
                    else: axs[axs_idx].set_ylabel(k+'_'+str(j+1))
                    axs_idx+=1
            else:
                sns.lineplot(x=plot_idx,y=samples_dict[k][plot_idx,0], palette="tab10", linewidth=.75, ax = axs[axs_idx])
                if k=='theta' and theta_names is not None: axs.set_ylabel(theta_names[0])
                else: axs[axs_idx].set_ylabel(k)
                axs_idx+=1
        if save is not None: plt.savefig(save,dpi=300, bbox_inches='tight')
        return fig
    else:
        lgds = []
        n_axes = len(samples_dict)-1 if 'theta_native' in samples_dict.keys() else len(samples_dict) # dont plot theta_native
        fig, axs = plt.subplots(n_axes,1,sharex=True,figsize=[10,1.5*n_axes])
        fig.subplots_adjust(hspace=0)
        for i, k in enumerate(samples_dict.keys()):
            if k == 'theta_native':
                continue
            n_lines = min(samples_dict[k].shape[1],max_print)
            if n_lines > 1:
                for j in range(n_lines):
                    sns.lineplot(x=plot_idx,y=samples_dict[k][plot_idx,j], palette="tab10", linewidth=.75, ax = axs[i],
                                label= theta_names[j] if (i==0 and theta_names is not None) else k+str(j+1))
                axs[i].set_ylabel(k)
                lgds.append(axs[i].legend(bbox_to_anchor=(1.025, 1), loc='upper left', borderaxespad=0., ncol=int(np.ceil(n_lines/5))))
            else:
                sns.lineplot(x=plot_idx,y=samples_dict[k][plot_idx,0], palette="tab10", linewidth=.75, ax = axs[i])
                axs[i].set_ylabel(theta_names[0] if (i==0 and theta_names is not None) else k)
        if save is not None: plt.savefig(save,dpi=300,bbox_extra_artists=lgds, bbox_inches='tight')
        return fig
         
def param_stats(samples_dict,theta_names=None,q1=0.05,q2=0.95,digits=4):
    """
    Compute statistics on the samples.

    :param dict samples_dict: samples from model.get_samples()
    :param list/NoneType theta_names: list of string names for thetas, optional (None will use default names)
    :param float q1: lower quantile in [0, 1]
    :param float q2: upper quantile in [0, 1]
    :param int digits: how many digits to show in output
    :return: pandas DataFrame containing statistics
    """
    # theta_names : list
    # samples_dict : dictionary of samples
    # stats : dataframe with mean and std of all parameters
    if 'theta' in samples_dict.keys():
        n_theta = samples_dict['theta'].shape[1]
        if theta_names is not None and len(theta_names) != n_theta:
            print('theta_names should have',n_theta, 'entries')
            return
    
    mean = []
    sd = []
    keys = []
    q1_list = []
    q2_list = []
    for i, k in enumerate(samples_dict.keys()):
        n_param = samples_dict[k].shape[1]
        for j in range(n_param):
            mean.append(np.round(np.mean(samples_dict[k][:, j]),digits))
            sd.append(np.round(np.std(samples_dict[k][:, j]),digits))
            q1_list.append(np.round(np.quantile(samples_dict[k][:, j],q1),digits))
            q2_list.append(np.round(np.quantile(samples_dict[k][:, j],q2),digits))
            if i==0 and theta_names is not None: keys.append(theta_names[j])
            elif n_param>1: keys.append(k+'_'+str(j+1))
            else: keys.append(k)
    stats = pd.DataFrame({'mean':mean,'sd':sd,'{} quantile'.format(q1):q1_list,\
                          '{} quantile'.format(q2):q2_list},index=keys)
    return stats

def rho_box_plots(model,labels=None):
    """
    Show rho box plots. (Rho are the transformed betaU parameters, corresponding to GP lengthscales)

    :param sepia.SepiaModel model: SepiaModel object
    :param list/NoneType labels: optional labels to use for box plot
    :return: matplotlib figure
    """
    samples_dict = {p.name: p.mcmc_to_array() for p in model.params.mcmcList}
    p = model.num.p
    q = model.num.q
    pu = model.num.pu
    bu = samples_dict['betaU']
    ru = np.exp(-bu / 4)
    fig,axs = plt.subplots(nrows=pu,tight_layout=True,figsize=[5,3*pu],squeeze=False)
    for i,ax in enumerate(axs.flatten()):
        r = ru[:, ((p+q)*i):((p+q)*i)+(p+q)]
        ax.boxplot(r)
        if labels is not None: ax.set_xticklabels(labels)
        ax.set_yticks(np.arange(0,1.2,.2))
        ax.set_ylabel(r'$\rho$')
        ax.set_title('PC {}'.format(i+1))
    return fig
        
def plot_acf(model,nlags,nburn=0,alpha=.05,save=None):
    """
    Plot autocorrelation function for all parameters theta.
    
    :param sepia.SepiaModel model: SepiaModel object
    :param int nlags: how many lags to compute/plot
    :param int nburn: how many samples to burn
    :param float alpha: confidence level for acf significance line (0,1)
    :param str save: file name to save figure
    :return: matplotlib figure
    """

    if nlags>model.get_num_samples():
        raise ValueError('plot_acf: must have more samples than requested lag size')

    if alpha <= 0 or alpha >= 1:
        raise ValueError('alpha must be in (0,1)')
    if model.num.sim_only:
        print('ACF needs thetas but this is a sim-only model.')
        return
    # get theta chains
    for p in model.params.mcmcList:
        if p.name == 'theta': 
            chain = p.mcmc_to_array(flat=True).T
    
    acf = model.acf(chain,nlags,plot=True,alpha=alpha)
    if save is not None: 
        acf['figure'].savefig(save,dpi=300,bbox_inches='tight')
    return acf
