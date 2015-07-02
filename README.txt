Materials Search Server and Webpage

Searches Materials Project and Web of Knowledge for relevant data with respect to finding promising new candidates for superconductivity.

######## RUNNING THE PROGRAM ########

This program requires installation of python.exe and several prerequisite modules.
Below is the list of prerequisite modules that must be installed via "pip install ____":
 - requests
 - beautifulsoup4
 - gevent
 - flask
 - git+git://github.com/amueller/word_cloud.git (substitute this phrase in the above command)

After these have been installed, run the server initialization with the line:

 python materialsSearch_Serv.py

or by double clicking and launching the compiled file:

    materialsSearch_Serv.pyc

The localhost server will then continue to run indefinitely until cancelled.
The user can cancel the server run by pressing Ctrl+C at the command line at any time.


######## USING THE PROGRAM ########

Once the server is running, navigate in your browser to "localhost:8051".

There are then two text areas for adding search queries to send to Materials Project and Web of Knowledge and keywords to look for in the relevant results.

Methods for adding search queries include:
 - Adding query information straight into the text area, seperating queries with a semicolon ";".
 - Clicking the "sets" checkboxes to add/remove preset arrays of materials.
 - Adding permutations via the periodic table. To do this, first select an element set [A-D] then click in the periodic table to set the elements for the program to iterate through. The "ABCD = " text area will then display the sets of elements you chose. Clicking "Add Permutation" will add this set to the query box and refresh your periodic table. The sets of elements represent the permutations of elements you selected (i.e. each set is crossed with each other set and the resulting set is added to the search list).

Methods for adding keywords include:
 - Adding keyword information straight into the text area, seperating queries with a semicolon ";".
 - Clicking "Reset Default" which will clear the keyword area and subsequently add the preset keywords.


There is a text area for naming the search. When the search is recorded for loading later, this is the name the file record will take and appear as in the future.
If this is left blank, the server will automatically generate a name according to the following metric: "search" + numSearch + '_' + ('mp'/'wok') where numSearch = the number of load files + 1

There is an area for changing the search limit. This is only relevant in a WoK search and it determines the number of results the program analyzes for each query.

Selecting a load file form the "Load a previous search:" dropdown and clicking "Load" will return the results of that search in the result area below.

Clicking "Search MP" will search Materials Project and clicking "Search WoK" will search Web of Knowledge. The respective results will be loaded below.

Clicking "Generate CSVs and WCs" will generate .csv files and wordclouds of the data and store them in \searchWoK\materialsSearchCSV-WC. Information about digesting these is below.


Clicking any of the 'submit' buttons (i.e. MP/WoK/CSVs and WCs) will send a POST request to the server for the python code to handle the request.
After each query search, the python code stores the search information in a cache file such that future searches of these items will not require searching time or internet connection.
However, if the majority of the entered queries are not in the cache, the program will take a long period of time to produce results. One can view the progress of the search by opening the Terminal or CMD prompt from which the program was launched.
Otherwise, if the server encounters an error, it will report that an error has been caught in the server status text area.
If the procedure finishes successfully, the server status box will report a cheerful 'Done!'.


######## Viewing the Webpage Results ########

The MP Results spit out a table of values and labels for the queries provided.
These can be sorted by clicking the table titles at the top.

 *NOTE* The sorting procedure pings the server just like the submit buttons. Therefore, a sorting command cannot be executed during an active search.

When the loaded MP and WoK searches have the same queries, both boxes will be returned sorted in the same order. Otherwise, only the MP will be sorted.

Under the 'Formula' title of the MP search lies hyperlinks to the MP search pages. Under 'CIF' are hyperlinks to the CIF data which can be saved by right clicking the link and clicking 'Save link as...'. The 'Model' buttons open the crystal structure in a new window.

Clicking the table rows will expand the data to show more detailed information.


The WoK Results return the formula, the number of publications, and lists of frequencies of respective keywords.
The 'Material' title holds hyperlinks to the WoK search pages. These may not work in most browsers due to WoK security protocol.

Clicking a WoK row will expand the data into a list of (num) hyperlinks where each link represents a different paper and num represents the number of times the keyword appeared in the abstract. The links will bring you to the journal page of the article.


######## Viewing the CSV/WC Results ########

Search Results can be found in \searchWoK\materialsSearchCSV-WC

Results consist of two .csv files and folders of WordCloud images.

<name>MaterialsSearchCondensed.csv is a condensed version of the search data, viewable all in one page. It lists material name, # of WoK result publications, crystal system, space group, calculated band gap, and then numbers according to how many paper's abstracts the script found the respective keywords. 

Clicking the material name or the keyword frequency numbers will bring you to the corresponding location in <name>MaterialsSearchFull.csv . This link will work as long as the ...Condensed.csv and ...Full.csv files are in the same folder.

<name>MaterialsSearchFull.csv lists all of the information available. It holds all  of the aforementioned data in ...Condensed.csv in addition to having seperate links to the WoK search results page, the WordCloud image, and cells listed as keyword(#). Each of these cells is reference to a different paper (clicking the cell will bring you to the journal's page on the paper). 'keyword' is obviously the keyword that came up in the paper's abstract and # is the number of times it came up.

The WoK results page link may not work the first time, as your browser needs to set up a session and get cookies from WoK. The second time in the same browser should work. The WordCloud image link will work as long as the <name> folder consisting of the images is in the same directory as <name>MaterialsSearchFull.csv. Lastly, some of the keyword(#) links may not work or may be listed as 'N/A' if the script couldn't find the journal link or the DOI.org server produced no results.
