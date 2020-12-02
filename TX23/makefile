###########################################################################
#     Sint Wind PI
#       Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

CFLAGS += -O0 -g

all : readTX23 libTX23.so

clean :
	$(RM) *.o readTX23 libTX23.so *~

readTX23 : RPi_TX23.o readTX23.o
	$(CC) $(CFLAGS) -o readTX23 RPi_TX23.o readTX23.o -lbcm2835 -lrt

libTX23.so : libTX23.o RPi_TX23.o 
	$(CC) $(CFLAGS) --shared -o libTX23.so libTX23.o RPi_TX23.o -lbcm2835 -lrt

# The next lines generate the various object files

libTX23.o : libTX23.c  RPi_TX23.c RPi_TX23.h
	$(CC) $(CFLAGS) -c libTX23.c
     
RPi_TX23.o : RPi_TX23.c RPi_TX23.h
	$(CC) $(CFLAGS) -c RPi_TX23.c

readTX23.o : readTX23.c RPi_TX23.h
	$(CC) $(CFLAGS) -c readTX23.c
