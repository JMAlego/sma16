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

ifdef MEMORY_FILE
MACRO_DEFINES += -D MEMORY_FILE=$(MEMORY_FILE)
endif

sma16vm: sma16vm.c $(MEMORY_FILE)
ifdef MEMORY_FILE
	cp $(MEMORY_FILE) memory_file.s16
endif
	gcc -Wall -pedantic sma16vm.c -o sma16vm $(MACRO_DEFINES)
ifdef MEMORY_FILE
	rm memory_file.s16
endif

.PHONY: asm clean build

asm: sma16vm.a

build: sma16vm

clean:
	rm -f sma16vm
