SRC_PYM = pym

PHONY =

PHONY += all
all:
	$(MAKE) -s format
	$(MAKE) -s check

PHONY += check
check:
	pyflakes $(SRC_PYM)

PHONY += format
format:
	black $(SRC_PYM)

.PHONY: $(PHONY)
