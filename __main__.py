from crawler import crawler
from storage import Storage

SEED = 'https://www.cpp.edu/engineering/ce/index.shtml'
NUM_PAGES = 13

def main():
    pages = crawler(SEED, NUM_PAGES)

# 5. Execution Block
if __name__ == "__main__":
    main()   