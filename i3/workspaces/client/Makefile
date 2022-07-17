CFLAGS=-g3 -Wall -W -Wno-parentheses -Wstrict-prototypes -Wmissing-prototypes -Wundef -Wredundant-decls -std=gnu99 -Wformat-truncation=0

all: i3-workspace

i3-workspace: LDLIBS+=$(shell pkg-config --libs xft) -lXext -lX11 

i3-workspace: LDLIBS+=-lX11

clean:
	rm -f *~ *.o i3-workspace

install:
	cp i3-workspace ~/bin

compile-install:
	$(MAKE) all
	sudo $(MAKE) install
