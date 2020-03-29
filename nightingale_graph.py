#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 28 18:26:00 2020
Reimplementation of notebook from luthars and lukas from abel ideas.
@author: lg
"""
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

def init_random(**options):
    '''Generate network according to assumed topology'''
    n = options.get('n')
    p = options.get('p')
    G = nx.erdos_renyi_graph(n, p, directed=False)
    return G

def init_stochastic_block_model(**options):
    '''Generate network according to assumed topology'''
    block_sizes = options.get('block_sizes')
    p_blocks = options.get('p_blocks')
    G = nx.generators.community.stochastic_block_model(block_sizes, p_blocks, seed=0)
    return G  

def init_barabasi_albert(**options):
    '''Generate network according to assumed topology'''
    n = options.get('n')
    k = options.get('k')
    G = nx.barabasi_albert_graph(n, k)
    return G

def network_init(network_type, **options):
    '''Generate network according to assumed topology'''
    # Choses between these models
    model_dict = {
        1: init_random,
        2: init_stochastic_block_model,
        3: init_barabasi_albert,
        }
    graph = model_dict.get(network_type, "nothing")
    return graph(**options)

def init_node_states(G, fraction_infected):
    healthy = 0
    infected = 1
#    recovered = 2
    n_infected = np.int(np.floor(fraction_infected * G.number_of_nodes()))

    # Initialize infected nodes
    # Randomly sample a subset from population corresponding to n_infected
    infected_nodes = np.random.choice(G.number_of_nodes(), n_infected, replace=False)
    state_vector = np.zeros(G.number_of_nodes()) + healthy
    state_vector[infected_nodes] = infected
    # Convert the array to dictionary of states
    state_dict = dict(enumerate(state_vector))
    
    # Initialize node states
    nx.set_node_attributes(G, state_dict, 'state')
    nx.set_node_attributes(G, 0, 'n_contacts')
    nx.set_node_attributes(G, 0, 'n_infected_contacts')
    nx.set_node_attributes(G, 0, 'infected_by')
    nx.set_node_attributes(G, 0, 'incubation_time')
    return G
    

def test_infection(p_infection):
    '''Only call function to test if infetcted person will infect a healthy one'''
    healthy = 0
    infected = 1
    return infected if np.random.random() < p_infection else healthy

def update_nodes(G, fraction_interacting, p_infection, p_contact, 
                 recovery_rate = 0, 
                 lockdown = False, people_met_in_lockdown = None, 
                 sociable = False):
    '''Set an interaction time point and update the node attributes'''
    healthy = 0
    infected = 1
    recovered = 2
    # Pick a subset of people to interact
    n_interacting = np.int(np.floor(fraction_interacting * G.number_of_nodes()))
    interacting_nodes = np.random.choice(G.number_of_nodes(), n_interacting, replace=False)
    
    # Loop only over the interacting nodes
    for i_node in interacting_nodes:
        for j_neighbor in iter(G[i_node]):
            # Test if the node meets the neighbor
            if np.random.random() < p_contact:
                # Since everyone starts with zero contacts, we can just sum up.
                G.nodes[i_node]['n_contacts'] =+ 1
                G.nodes[j_neighbor]['n_contacts'] =+ 1
                # Now if contact involves infected person
                # Since everyone starts with zero contacts, we can just sum up.
                if G.nodes[i_node]['state'] == healthy and \
                G.nodes[j_neighbor]['state'] == infected:
                    G.nodes[i_node]['n_infected_contacts'] =+ 1
                    G.nodes[i_node]['state'] = test_infection(p_infection)
                elif G.nodes[i_node]['state'] == infected and \
                G.nodes[j_neighbor]['state'] == healthy:
                    G.nodes[j_neighbor]['n_infected_contacts'] =+ 1
                    G.nodes[j_neighbor]['state'] = test_infection(p_infection)
                elif G.nodes[i_node]['state'] == infected and \
                G.nodes[j_neighbor]['state'] == infected:
                    G.nodes[i_node]['n_infected_contacts'] =+ 1
                    G.nodes[j_neighbor]['n_infected_contacts'] =+ 1        
    
    return G


#%%
    
# Define graph parameters
options = {
        'n': 600,
        'p': 0.1,
        'k': 3,
        'directed': False,
        'block_sizes': [200, 200, 200],
        'p_blocks': [[0.8, 0, 0.8], 
                     [0, 0, 0], 
                     [0.8, 0, 0.1]]
        }

## Parameters defining lockdown
## Fraction of people interacting each time point
#fraction_interacting = 0.1
#n_contacts = 4 # Average household size
#fraction_contact = 0.1

# Normal situation
initial_fraction_infected = 0.1
fraction_interacting = 0.1
p_infection = 0.02
p_contact = 0.2

# Definition of states, maybe a global constant can be defined
healthy = 0
infected = 1
recovered = 2

# Number of simulation times
n_sim_times = 60

# Create random graph
G_rand_sbm = network_init(1, **options)
# Create stochastic block model
G_sbm = network_init(2, **options)
# Add block connections to random graph
G_rand_sbm.add_edges_from(G_sbm.edges())
G_rand_sbm = G_rand_sbm.to_undirected()

n_infected = np.zeros(n_sim_times)

# Initialize network
G = init_node_states(G_rand_sbm, fraction_infected=initial_fraction_infected)
# Extract node states, will make a method
states = np.array(list(nx.get_node_attributes(G, 'state').values()))
n_infected[0] = np.size(np.where(states == infected))

# Run the simulation assuming one timestep per day
for i_time in np.arange(1, n_sim_times):
    G = update_nodes(G, fraction_interacting=fraction_interacting, 
                 p_infection=p_infection, p_contact=p_contact)
    # Extract node states, will make a method
    states = np.array(list(nx.get_node_attributes(G, 'state').values()))
    n_infected[i_time] = np.size(np.where(states == infected))
    #nx.draw_spring(G, cmap=plt.get_cmap('viridis'), node_color=states)
    
plt.plot(n_infected)
plt.xlabel('Time step (days)')
plt.ylabel('Number of infected people')
#%%
plt.figure(num=1)

plt.spy(nx.adjacency_matrix(G_sbm))
