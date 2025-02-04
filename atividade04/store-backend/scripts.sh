#!/bin/bash

# List of Python scripts to run
SCRIPTS=("principal.py" "entrega.py" "estoque.py" "pagamento.py")

# Loop through scripts and open a new terminal for each
for script in "${SCRIPTS[@]}"; do
    gnome-terminal -- bash -c "python3 $script; exec bash"
done