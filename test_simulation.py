#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 19:45:46 2020

@author: lg
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 28 18:26:00 2020
Test script of the nightingale graph model
@author: lg
"""

import nightingale as ng
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt


#%%
# Definition of states, inherit the definitions used in the nightingale module.
healthy = ng.healthy
infected = ng.infected
recovered = ng.recovered


#%% Define graph parameters

random_encounters = 0.01 # Probability that people meet at random, Possible values between [0,1] 
prob_communities = [0.1, .01, .01, .005, .001, 0, 0, 0] # Possible values between [0,1] 
# First three entries are the probability meet in a community, 
# while the last three entries is the probability of different communities meet
# Probabilities  between individuals within community 1,2,3 are represented in the entries 0,1,2,respectively.
# Probability between individuals between community 1 and 2 is entry 3
# Probability between individuals between community 1 and 3 is 4
# Probability between individuals between community 2 and 3 is 5
# Generate the probability matrix, actually a list of lists.
prob_blocks = [ [prob_communities[0], prob_communities[3], prob_communities[4] ] , 
                [prob_communities[3], prob_communities[1], prob_communities[5] ] ,
                [prob_communities[4], prob_communities[5], prob_communities[2] ] ]

# Define size of communities and network
block_sizes = [200, 100, 800]
graph_size = sum(block_sizes)

initial_fraction_infected = 0.08  # Percentage of the population initially infected.  Possible values between [0,1]  
fraction_interacting = 0.9 # Percentate of people interacting in each period. # Possible values between [0,1] 
p_infection = 0.1 # likelyhood that a sick people infect a healthy person (Susceptible) if they interact. 
p_contact = 0.01 # Possible values between [0,1] 
    
# Define graph parameters
options = {
        'n': graph_size,
        'p': random_encounters,
        'k': 3,
        'directed': False,
        'block_sizes': block_sizes,
        'p_blocks': prob_blocks # Matrix needs to be symmetric!
        }

## Parameters defining lockdown
## Fraction of people interacting each time point
#fraction_interacting = 0.1
#n_contacts = 4 # Average household size
#fraction_contact = 0.1

# Normal situation
initial_fraction_infected = 0.1
fraction_interacting = 0.1
p_infection = 0.1
p_contact = 0.2


recovery_time = 21
contagious_time = 14


# Number of simulation times
n_sim_times = 100


#%% Create graph structure.
# Create random graph
G_rand_sbm = ng.network_init(1, **options)
# Create stochastic block model
G_sbm = ng.network_init(2, **options)
# Add block connections to random graph
G_rand_sbm.add_edges_from(G_sbm.edges())
G_rand_sbm = G_rand_sbm.to_undirected()

#%% Initialize network
G = ng.init_node_states(G_rand_sbm, fraction_infected=initial_fraction_infected)
# Extract node states, will make a method
n_infected = np.zeros(n_sim_times)
n_recovered = np.zeros(n_sim_times)

states = np.array(list(nx.get_node_attributes(G, 'state').values()))
n_infected[0] = np.size(np.where(states == infected))
n_recovered[0] = np.size(np.where(states == recovered))

# Run the simulation assuming one timestep per day
for i_time in np.arange(1, n_sim_times):
    G = ng.update_nodes(G, fraction_interacting=fraction_interacting, 
                 p_infection=p_infection, p_contact=p_contact, 
                 recovery_time=recovery_time, contagious_time=contagious_time)
    # Extract node states, will make a method
    states = np.array(list(nx.get_node_attributes(G, 'state').values()))
    n_infected[i_time] = np.size(np.where(states == infected))
    n_recovered[i_time] = np.size(np.where(states == recovered))

    #nx.draw_spring(G, cmap=plt.get_cmap('viridis'), node_color=states)
#%%   
plt.plot(n_infected, label='infected')
plt.plot(n_recovered, label='recovery')
plt.xlabel('Time step (days)')
plt.ylabel('Number of infected people')
plt.legend()
#%%
#plt.figure(num=1)
#
#plt.spy(nx.adjacency_matrix(G_sbm))
