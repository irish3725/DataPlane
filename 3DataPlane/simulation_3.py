'''
Created on Oct 12, 2016

@author: mwitt_000
'''
import network_3 as network
import link_3 as link
import threading
from time import sleep

def payload(length=39):
    pay = ''
    # change range to 39 for 80 bytes
    # change range to 26 for 74 bytes
    # change range to 21 for 44 bytes
    for i in range(length):
        pay += str(i)
    return pay

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 10 #give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = [] #keeps track of objects, so we can kill their threads
   
    # create routing table
    A_table = [['00001', '*', 0], ['00002', '*', 1]]
    B_table = [['*', '*', 0]] 
    C_table = [['*', '*', 0]] 
    D_table = [['*', '00003', 0], ['*', '00004', 1]]
 
    #create network nodes
    client_1 = network.Host(1)
    object_L.append(client_1)
    client_2 = network.Host(2)
    object_L.append(client_2)
    server_3 = network.Host(3)
    object_L.append(server_3)
    server_4 = network.Host(4)
    object_L.append(server_4)
    router_a = network.Router(name='A', intf_count=2, max_queue_size=router_queue_size, route_table=A_table)
    object_L.append(router_a)
    router_b = network.Router(name='B', intf_count=1, max_queue_size=router_queue_size, route_table=B_table)
    object_L.append(router_b)
    router_c = network.Router(name='C', intf_count=1, max_queue_size=router_queue_size, route_table=C_table)
    object_L.append(router_c)
    router_d = network.Router(name='D', intf_count=2, max_queue_size=router_queue_size, route_table=D_table)
    object_L.append(router_d)
    
    #create a Link Layer to keep track of links between network nodes
    link_layer = link.LinkLayer()
    object_L.append(link_layer)
    
    #add all the links
    link_layer.add_link(link.Link(client_1, 0, router_a, 0, 50))
    link_layer.add_link(link.Link(client_2, 0, router_a, 1, 50))
    link_layer.add_link(link.Link(router_a, 0, router_b, 0, 30))
    link_layer.add_link(link.Link(router_a, 1, router_c, 0, 30))
    link_layer.add_link(link.Link(router_b, 0, router_d, 0, 30))
    link_layer.add_link(link.Link(router_c, 0, router_d, 1, 30))
    link_layer.add_link(link.Link(router_d, 0, server_3, 0, 30))
    link_layer.add_link(link.Link(router_d, 1, server_4, 0, 30))
    
    #start all the objects
    thread_L = []
    thread_L.append(threading.Thread(name=client_1.__str__(), target=client_1.run))
    thread_L.append(threading.Thread(name=client_2.__str__(), target=client_2.run))
    thread_L.append(threading.Thread(name=server_3.__str__(), target=server_3.run))
    thread_L.append(threading.Thread(name=server_4.__str__(), target=server_4.run))
    thread_L.append(threading.Thread(name=router_a.__str__(), target=router_a.run))
    thread_L.append(threading.Thread(name=router_b.__str__(), target=router_b.run))
    thread_L.append(threading.Thread(name=router_c.__str__(), target=router_c.run))
    thread_L.append(threading.Thread(name=router_d.__str__(), target=router_d.run))
    
    thread_L.append(threading.Thread(name="Network", target=link_layer.run))
    
    for t in thread_L:
        t.start()
    
    
    #create some send events    
#    for i in range(3):
        # send strings that are increasing in size up to 80B
#        client_1.udt_send(3, 'Sample data %s' % payload((i+1)*13))
    client_1.udt_send(3, '___1-3___')
    client_1.udt_send(4, '___1-4___')
    client_2.udt_send(3, '___2-3___')
    client_2.udt_send(4, '___2-4___')
#    client_1.udt_send(3, '___1-3___ %s' % payload(100))
#    client_1.udt_send(4, '___1-4___ %s' % payload(100))
#    client_2.udt_send(3, '___2-3___ %s' % payload(100))
#    client_2.udt_send(4, '___2-4___ %s' % payload(100))
    
    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)
    
    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()
        
    print("All simulation threads joined")



# writes to host periodically
