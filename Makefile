MACRO_DEFINES ?=

ifdef DISABLE_TIMING
MACRO_DEFINES += -D DISABLE_TIMING
endif

ifdef DISABLE_DEBUG
MACRO_DEFINES += -D DISABLE_DEBUG
endif

ifdef DISABLE_SIGINT
MACRO_DEFINES += -D DISABLE_SIGINT
endif

sma16vm: program.s16 sma16vm.c
	gcc -Wall -pedantic sma16vm.c -o sma16vm $(MACRO_DEFINES)

.PHONY: asm clean build

asm: sma16vm.a

build: sma16vm

clean:
	rm -f sma16vm.a
	rm -f sma16vm

sma16vm.a: program.s16 sma16vm.c
	gcc -S -fverbose-asm -Wall -pedantic sma16vm.c -o sma16vm.a $(MACRO_DEFINES)
