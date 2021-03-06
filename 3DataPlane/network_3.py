'''
Created on Oct 12, 2016

@author: mwitt_000
'''
import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
        self.mtu = None
    
    ##get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)
        
## Implements a network layer packet (different from the RDT packet 
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths 
    src_addr_S_length = 5 
    dst_addr_S_length = 5
    ID_length = 2
    fragflag_length = 1
    offset_length = 5 
    head_length = 18
    
    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    def __init__(self, src_addr, dst_addr, ID, fragflag, offset, data_S):
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.ID = ID
        self.fragflag = fragflag
        self.offset = offset
        self.data_S = data_S
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.src_addr).zfill(self.src_addr_S_length)
        byte_S += str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += str(self.ID).zfill(self.ID_length)
        byte_S += str(self.fragflag).zfill(self.fragflag_length)
        byte_S += str(self.offset).zfill(self.offset_length)
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        src_addr = int(byte_S[0:NetworkPacket.src_addr_S_length])
        off = NetworkPacket.src_addr_S_length 
        dst_addr = int(byte_S[off:off+NetworkPacket.dst_addr_S_length])
        # to keep track of an offset so I don't have to add
        # up a new offset in every line
        off = NetworkPacket.dst_addr_S_length
        ID = int(byte_S[off:off+NetworkPacket.ID_length])
        # get fragmentation flag        
        off += NetworkPacket.ID_length
        fragflag = int(byte_S[off:off+NetworkPacket.fragflag_length])
        # get offset
        off += NetworkPacket.fragflag_length 
        offset = int(byte_S[off:off+NetworkPacket.offset_length])
        # get payload
        data_S = byte_S[self.head_length : ]
        return self(src_addr, dst_addr, ID, fragflag, offset, data_S)

    def ceiling(a, b):
        result = float(a) / float(b)
#        print('get_float %f' % result)
        if result % 1 != 0:
            return int(result) + 1
        return int(result)   
   

## Implements a network host for receiving and transmitting data
class Host:
   
    # ID of next packet
    ID = 0
    # store message if incomplete
    message = ''
 
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)
       
    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S):
#        print('get_data_S: %s' % data_S)       
        payload_size = len(data_S.encode('utf-8')) 
               
        # get number of segments needed
        segments = NetworkPacket.ceiling(payload_size, (self.out_intf_L[0].mtu - NetworkPacket.head_length))
        # divide into segments of size mtu and send as packets
        for i in range(segments):
            # where to start string
            offset = i * (self.out_intf_L[0].mtu - NetworkPacket.head_length)
            # where to stop string
            end = (i + 1) * (self.out_intf_L[0].mtu - NetworkPacket.head_length)
#            print('offset is %d and end is %d' % (offset,end))
            fragflag = 1 
            if end >= payload_size:
                fragflag = 0
            #using self.addr as source address
            p = NetworkPacket(self.addr, dst_addr, self.ID, fragflag, offset, data_S[offset:end])
            self.out_intf_L[0].put(p.to_byte_S()) #send packets always enqueued successfully
            print('%s: sending packet "%s" out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))

            # if we are done with this message
            if fragflag is 0:
                # incriment ID without making it more than 2 
                # characters when we are done with message
                self.ID = (self.ID + 1) % 100 


            

    ## receive packet from the network layer
    def udt_receive(self): 
        pkt_S = self.in_intf_L[0].get() 
        if pkt_S is not None:
            if self.message is '':
                # set message to the entire received packet
                # keeping the header and marking it as not
                # segmented
                self.message = pkt_S
#                self.message[7] = '0' 
                if pkt_S[12] is '0':
                    # if message is not segmented, print and reset 
                    print('%s: received packet "%s"' % (self, self.message))
                    self.message = '' 
            elif pkt_S[12] is '1':
                # concat the payload onto current message 
                # and wait for next packet 
                self.message += pkt_S[18:] 
            else:           
                # concat the payload onto current message,
                # we are done now, so print final message,
                # reset message variable 
                self.message += pkt_S[18:]
                print('%s: received packet "%s"' % (self, self.message))
                self.message = ''
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router described in class
class Router:
    
    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces 
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_count, max_queue_size, route_table):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.route_table = route_table

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    # appropriate outgoing interfaces
    def forward(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                #get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                #if packet exists make a forwarding decision
                if pkt_S is not None:
#                    print('get_pkt_S: %s' % pkt_S) 
                    payload_length = len(pkt_S[18:].encode('utf-8'))
                    segments = NetworkPacket.ceiling(payload_length, (self.out_intf_L[i].mtu - NetworkPacket.head_length))
#                    print('get_paylength: %d, get_mtu: %d' % (payload_length, self.out_intf_L[i].mtu - NetworkPacket.head_length)) 
                    # get packet's header values
                    src_addr = pkt_S[:5]
                    dst_addr = pkt_S[5:10]
                    ID = pkt_S[10:12]
                    fragflag = pkt_S[12]
                    offset = pkt_S[13:18]    
                    payload = pkt_S[18:]
                    # set intf to bogus value so it crashes
                    # when rule isn't found 
                    intf = 1000000000 
                    # iterate through each rule 
                    for rule in self.route_table:
                        # if first value matches src_addr 
                        if rule[0] is '*' or rule[0] == src_addr:
                            # and second rule matches dst_addr 
                            if rule[1] is '*' or rule[1] == dst_addr:
                                # then set interface to third rule 
                                intf = rule[2] 
                                # don't keep cycling through rules 
                                break
                    # send each segment
                    for s in range(segments):
                        # get start and end offset values for payload
                        start = s * (self.out_intf_L[i].mtu - NetworkPacket.head_length)
                        end = (s + 1) * (self.out_intf_L[i].mtu - NetworkPacket.head_length)
                                                
#                        print('get_segments: %d, get_s: %d, get_start: %d, get_end: %d' % (segments, s, start, end))
                        # new fragmentation flag
                        nfragflag = '1'
                        # set new fragmentation flag to 0
                        # if and only if the old frag flag
                        # was 0 and this is the last segment
                        # of this packet
                        if fragflag is '0' and end >= payload_length:
                            nfragflag = '0'
                        p = NetworkPacket(src_addr, dst_addr, ID, nfragflag, str(int(offset) + start), payload[start:end])
#                        print('get_packet %s' % p)
#                        p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                        # HERE you will need to implement a lookup into the 
                        # forwarding table to find the appropriate outgoing interface
                        # for now we assume the outgoing interface is also i
                        self.out_intf_L[intf].put(p.to_byte_S(), True)
                        print('%s: forwarding packet "%s" from interface %d to %d with mtu %d' \
                            % (self, p, i, intf, self.out_intf_L[intf].mtu))
            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, intf))
                pass
                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 
