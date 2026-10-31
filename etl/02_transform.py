# -*- coding: utf-8 -*-
"""CLI da fase de tratamento.

Uso:
    python etl/02_transform.py
    python etl/02_transform.py --uf AC
    python etl/02_transform.py --uf AC SP --nrows 5000
"""

from transformar import main

if __name__ == "__main__":
    main()
