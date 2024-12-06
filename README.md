This is a backup of an old project that used a Raspberry Pi to display content on two eink displays via IT8951 e-paper controller, used GPIO buttons to control the content. The code completed the logic of saving the created pages and navigating pages using the buttons. However, some modules such as socialmedia_scraper are not working due to missing code. 

# Setup environment
1. suggest using anaconda for environment management. python >= 3.8 is required.

    `conda create -n <name of env> python=3.8`

2. install the dependencies
    
    a. first activate the conda environment
        `conda activate <name of env>`
    
    b. move to the directory where the requirements.txt is

    c. install the dependencies
        `pip install -r requirements.txt`

3. run demo program

    `python main.py -v -d`

    -v for running virtually and -d for loading demo pages
    
    you can run `python main.py --help` to see the full list of arguments

4. a chrome executable is also required
 
