CFLAGS=-g3 -Wall -W -Wno-parentheses -Wstrict-prototypes -Wmissing-prototypes -Wundef -Wredundant-decls -std=gnu99 -Wformat-truncation=0

all: i3-workspace

i3-workspace: LDLIBS+=$(shell pkg-config --libs xft) -lXext -lX11 
i3-workspace: LDLIBS+=-lX11
i3-workspace.o: i3-workspace.c data.c

data.c: gen_c.py i3_workspace_util.py i3_workspace_help.py i3_workspace_constants.py i3_workspace_main_functions.py
	./gen_c.py > data.c


clean:
	rm -f *~ *.o i3-workspace data.c

install:
	cp i3-workspace ~/bin

compile-install:
	$(MAKE) all
	sudo $(MAKE) install
