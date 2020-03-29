#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 28 18:26:00 2020
Module for simulating abm graph dynamics for pandemics modeling
@author: lg
"""
import networkx as nx
import numpy as np


# Define global state definitions

healthy = 0
infected = 1
recovered = 2

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
#    healthy = 0
#    infected = 1
##    recovered = 2
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
    nx.set_node_attributes(G, 0, 'time_infected')
    return G
    

def test_infection(p_infection):
    '''Only call function to test if infetcted person will infect a healthy one'''
    healthy = 0
    infected = 1
    return infected if np.random.random() < p_infection else healthy

def update_time_infected(G):
    infected = 1
    '''Update time a node has been infected'''
    infected_nodes = [n for n, v in G.nodes(data=True) if v['state'] == infected]  
    for i_node in infected_nodes:
        G.nodes[i_node]['time_infected'] += 1
    return G
        
def check_recovery(G, recovery_time):
    infected = 1
    recovered = 2
    '''Check if a node reached recovery time'''
    infected_nodes = [n for n, v in G.nodes(data=True) if v['state'] == infected]
    # If the node recovers reset the time_infected.
    for i_node in infected_nodes:
        if G.nodes[i_node]['time_infected'] >= recovery_time:
            G.nodes[i_node]['time_infected'] = 0
            G.nodes[i_node]['state'] = recovered
    return G
        
def update_nodes(G, fraction_interacting, p_infection, p_contact, 
                 recovery_time = 0, contagious_time = 1000,
                 lockdown = False, people_met_in_lockdown = None, 
                 sociable = False):
    '''Set an interaction time point and update the node attributes'''
#    healthy = 0
#    infected = 1
#    recovered = 2
    # Pick a subset of people to interact
    n_interacting = np.int(np.floor(fraction_interacting * G.number_of_nodes()))
    interacting_nodes = np.random.choice(G.number_of_nodes(), n_interacting, replace=False)
    
    # First check if the person recovers this time point.
    G = update_time_infected(G)
    G = check_recovery(G, recovery_time)
    
    
    # Loop only over the interacting nodes
    for i_node in interacting_nodes:
        for j_neighbor in iter(G[i_node]):
            # Test if the node meets the neighbor
            if np.random.random() < p_contact:
                # Since everyone starts with zero contacts, we can just sum up.
                G.nodes[i_node]['n_contacts'] += 1
                G.nodes[j_neighbor]['n_contacts'] += 1
                # Now if contact involves infected person
                # Since everyone starts with zero contacts, we can just sum up.
                # Test if neighbor infects node
                if G.nodes[i_node]['state'] == healthy and \
                G.nodes[j_neighbor]['state'] == infected:
                    G.nodes[i_node]['n_infected_contacts'] += 1
                    if G.nodes[j_neighbor]['time_infected'] <= contagious_time:
                        G.nodes[i_node]['state'] = test_infection(p_infection)
                    if G.nodes[i_node]['state'] == infected:
                        G.nodes[i_node]['infected_by'] = j_neighbor
                # Test if node infects neighbor
                elif G.nodes[i_node]['state'] == infected and \
                G.nodes[j_neighbor]['state'] == healthy:
                    G.nodes[j_neighbor]['n_infected_contacts'] += 1
                    if G.nodes[i_node]['time_infected'] <= contagious_time:
                        G.nodes[j_neighbor]['state'] = test_infection(p_infection)
                    if G.nodes[j_neighbor]['state'] == infected:
                        G.nodes[j_neighbor]['infected_by'] = i_node
                # Update interaction between two infected nodes
                elif G.nodes[i_node]['state'] == infected and \
                G.nodes[j_neighbor]['state'] == infected:
                    G.nodes[i_node]['n_infected_contacts'] += 1
                    G.nodes[j_neighbor]['n_infected_contacts'] += 1        
    
    return G

