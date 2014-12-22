pyeucracy
=========

A collection of Python scripts for scraping data from the E-COST pages, to get
the data into other formats.

Currently, only has one script:
* get_payment_details.py: Given the URL for a meeting, gets the list of people
  with completed claims who haven't been paid yet, and loops through them,
  downloading their payment details, which are then saved in a temporary LaTeX
  file, which is included in a template .tex file. This can be used to populate
  forms. I wrote it because our Finance office only gives us PDF forms to fill
  in. So I do some hacky magic with `pdfpages` and `tikz` inside of latex.

Requirements:
-------------
* TeX Suite: with pdflatex command, pdfpages and tikz packages
* Python 2
* html5lib python package
* BeautifulSoup 4 python package

Basic usage:
------------

    ./get_payment_details.py -u USERNAME -p PASSWORD \
                             -l path/to/latex/template (without .tex extension)\
                             http://e-services.cost.eu/path/to/meeting/URL

Assuming it's working right, after a couple of seconds you should start to see
loads of LaTeX compiler output. It'll do that for every payment claim. When the
script's done, look in the forms/ directory. You should have some files with the
naming pattern

    payment.PAYMENTID.name_of_person.pdf


Configuring
-----------
Look inside of `get_payment_details.py`; there's a `defaults` variable, as well
as a `keys` variable inside of the `to_latex` function. You can tinker with
these to get different variable names for your latex output.
