#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 19:45:46 2020
Simulation script to be used in the web application.
@author: lg, luthi, abel
"""

import nightingale as ng
import networkx as nx
import numpy as np
import pandas as pd
import json


#%% Substitute by API input
#Define user inputs, all quantities are probabilities, valid values 0-1
# Probability that people meet at random.
random_encounters = 0.01 
# Probabilities of interaction between communities first within then between:
# 1-1, 2-2, 3-3, 1-2, 1-3, 2-3. 
prob_communities = [0.1, .01, .01, .005, .001, 0]
# Percentage of the population initially infected.
initial_fraction_infected = 0.08
# Percentate of people interacting in each period.
fraction_interacting = 0.9
# Probability that a infected person infects a healthy person (Susceptible) if they interact. 
p_infection = 0.1
# Probability that a person will interact with the neighbors.
p_contact = 0.01
# End definind user inputs, should come from the API.
#%%
# Definition of states, inherit the definitions used in the nightingale module.
healthy = ng.healthy
infected = ng.infected
recovered = ng.recovered

def create_rand_sbm_graph(**options):
    # Create random graph
    G_rand_sbm = ng.network_init(1, **options)
    # Create stochastic block model
    G_sbm = ng.network_init(2, **options)
    # Add block connections to random graph
    G_rand_sbm.add_edges_from(G_sbm.edges())
    G_rand_sbm = G_rand_sbm.to_undirected()
    return G_rand_sbm


def run_abm_simulation(random_encounters, prob_communities, 
                       initial_fraction_infected=0.1, fraction_interacting=0.1,
                       p_infection=0.3, p_contact=0.2):
    '''Run model simulation with user inputs. Models a random network with a 
    stochastic block model structure. We simulate 3 communities of 100 people
    each assuming fixed recovery contagiousness times.'''
    # Define size of communities and network
    block_sizes = [100, 100,100]
    graph_size = sum(block_sizes)
    # Probabilities of interaction between communities first within then between:
    # 1-1, 2-2, 3-3, 1-2, 1-3, 2-3, are stored in prob_communities.
    # Generate the probability matrix, actually a list of lists.
    prob_blocks = [ [prob_communities[0], prob_communities[3], prob_communities[4] ] , 
                    [prob_communities[3], prob_communities[1], prob_communities[5] ] ,
                    [prob_communities[4], prob_communities[5], prob_communities[2] ] ]
        
    # Define graph parameters
    options = {
            'n': graph_size,
            'p': random_encounters,
            'k': 3,
            'directed': False,
            'block_sizes': block_sizes,
            'p_blocks': prob_blocks # Matrix needs to be symmetric!
            }
        
    # Infection dynamics parameters    
    recovery_time = 8
    contagious_time = 7

    # Number of simulation times
    n_sim_times = 100
    
    # Create graph structure.
    G_rand_sbm = create_rand_sbm_graph(**options)
    # Initialize network
    G = ng.init_node_states(G_rand_sbm, fraction_infected=initial_fraction_infected)
    # Initialize variables of interest
    n_infected = np.zeros(n_sim_times)
    n_recovered = np.zeros(n_sim_times)
    n_infected_per_comm = np.zeros((n_sim_times, len(block_sizes)))
    n_recovered_per_comm = np.zeros((n_sim_times, len(block_sizes)))
    # Extract node states, will make a method
    states = np.array(list(nx.get_node_attributes(G, 'state').values()))
    n_infected[0] = np.size(np.where(states == infected))
    n_recovered[0] = np.size(np.where(states == recovered))
    # Split data by community, delete empty array at the end of the split output.
    states_per_comm = np.split(states, np.cumsum(block_sizes))[:len(block_sizes)]
    for i_comm in range(len(block_sizes)):
        n_infected_per_comm[0, i_comm] = np.size(np.where(states_per_comm[i_comm] == infected))
        n_recovered_per_comm[0, i_comm] = np.size(np.where(states_per_comm[i_comm] == recovered))
    # Run the simulation assuming one timestep per day
    for i_time in np.arange(1, n_sim_times):
        G = ng.update_nodes(G, fraction_interacting=fraction_interacting, 
                     p_infection=p_infection, p_contact=p_contact, 
                     recovery_time=recovery_time, contagious_time=contagious_time)
        # Extract node states, will make a method
        states = np.array(list(nx.get_node_attributes(G, 'state').values()))
        n_infected[i_time] = np.size(np.where(states == infected))
        n_recovered[i_time] = np.size(np.where(states == recovered))
        # Split data by community, delete empty array at the end of the split output.
        states_per_comm = np.split(states, np.cumsum(block_sizes))[:len(block_sizes)]
        for i_comm in range(len(block_sizes)):
            n_infected_per_comm[i_time, i_comm] = np.size(np.where(states_per_comm[i_comm] == infected))
            n_recovered_per_comm[i_time, i_comm] = np.size(np.where(states_per_comm[i_comm] == recovered))
        #nx.draw_spring(G, cmap=plt.get_cmap('viridis'), node_color=states)
    # Normalize the number of infected/recovered by the size of the community
    p_infected = n_infected / graph_size
    p_infected_per_comm = n_infected_per_comm / block_sizes
    p_recovered = n_recovered / graph_size
    p_recovered_per_comm = n_recovered_per_comm / block_sizes
    p_infected_and_recovered_per_com = p_infected_per_comm + p_recovered_per_comm
    
    output_table = pd.DataFrame({'time':range(n_sim_times), 
                                 'p_infected':p_infected,
                                 'p_infected_comm1':p_infected_per_comm[:, 0],
                                 'p_infected_comm2':p_infected_per_comm[:, 1],
                                 'p_infected_comm3':p_infected_per_comm[:, 2],
                                 'p_infected_and_recovered':p_infected + p_recovered,
                                 'p_infected_and_recovered_comm1':p_infected_and_recovered_per_com[:, 0],
                                 'p_infected_and_recovered_comm2':p_infected_and_recovered_per_com[:, 1],
                                 'p_infected_and_recovered_comm3':p_infected_and_recovered_per_com[:, 2],                                
                                 })
    # Save to file
    output_table.to_json('virus_evol.json')
    output_table.to_csv('virus_evol.csv')
    # Graph as JSON file
    # serialize graph data
#    with open('data.json', 'w') as outfile:
#        json.dump(nx.readwrite.json_graph.node_link_data(G), outfile)
    node_link_dict = nx.readwrite.json_graph.node_link_data(G)
    with open('graph_data.json', 'w') as outfile:
        outfile.write(json.dumps(node_link_dict))
    return
    
#%% Finally call the function to get the data files as output.
    
run_abm_simulation(random_encounters, prob_communities, 
                   initial_fraction_infected=0.1, fraction_interacting=0.1,
                   p_infection=0.3, p_contact=0.2)
