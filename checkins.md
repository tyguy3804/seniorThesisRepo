## Week 1 Summary (09/22/2025)

### This week I worked on:

I mainly have been extracting ERA5 data which I plan on using to train my model on. On Monday I added three use cases to my README.md but I would like to review them to make sure they are good enough.

### This week I learned:

That extracting data from an API takes longer than I expexted. One file takes up to 5 mintutes to extract but that really just means I need to run the extraction program more throughout the week. I also learned that instead of having seperate loops for pressure level and surface level data it would be better to retrieve both data in the same loop.

### My successes this week were:

I have extracted three years of data so far but would like to have more by now. 

### The challenges I faced this week were:

Looping through thirty-five years of data might take longer than I expexted, especially since I have to make two seperate datasets.

---

## Week 2 Summary (09/29/2025)
### This week I worked on:

Updated my extraction program so that I'm getting surface and pressue data in the same loop. Almost completed my HRRR extraction program. Began working on the MetPy calculations program.

### This week I learned:

How Herbie, an hrrr data extraction python package, works and also how HRRR data looks like. Learned some new regular expressions that Herbie uses to collect the correct data.

### My successes this week were:

I have been extracting more ERA5 data than I have last week and it has been much smoother as well. Not just have I been extracting more ERA5 data, I've gotten my hrrr extraction program up and running and I'm extracting the correct data as well.


### The challenges I faced this week were:

The most challenging part so far was figuring out how HRRR extraction worked and I had to tinker with the process of extacting the days, times, and variables I wanted. For example, getting data on different altitude levels (EX: 2m and 10m) wasn't allowed if I wanted one singular dataset (It would make a list of two seperate datasets). Going along with the struggle with HRRR extraction it took me awhile to create regular expressions that I send into the Herbie object that allows it to get the correct data.

---

## Week 3 Summary (10/06/2025)
### This week I worked on:

Continued working on my metpy calculations mainly for era5 data. Also continued downloading data for both HRRR and ERA5.

### This week I learned:

Learned a lot about how to use the metpy library and also how I wanted to somewhat format my dataset for my model. Needed to experiment with my data variables from the era5 data so that they could be used in the metpy functions.

### My successes this week were:

Continued to extract data and started to look in the future towards how I want my calculated and model-ready data to look like.

### The challenges I faced this week were:

Learning a new library of functions and making sure that I would get the correct outputs.

---

## Week 4 Summary (10/13/2025)
### This week I worked on:

Completed working on metpy calculations for era5 data. 

### This week I learned:

More about the metpy library

### My successes this week were:

Getting closer to having all my data and being able to make some important calculations that I will be using for my model.

### The challenges I faced this week were:

Trying to tinker with metpy calculations and also collecting those outputs for all era5 data that I have.

---

## Week 5 Summary (10/20/2025)
### This week I worked on:

Started working on calculations for hrrr data (mostly the same as era5 but some slight differences). Made tweaks to my hrrr data extraction program.

### This week I learned:

That some values that I have extracted weren't neccessary for any calculations. They didn't take up much space or time so not too much to worry about. I also learned that the regular expressions I have been using to tell Herbie, the hrrr data extractor, weren't working properly and left out some data. (For example, it left out temperature and dewpoint data and also didn't use the correct pressure values too.)

### My successes this week were:

Continued to extract era5 data.

### The challenges I faced this week were:

I needed to re-extract all my hrrr data because of mutiple reasons. I should have checked sooner but since I started looking at using hrrr data for my calculations I noticed that the data just wasn't right and noticed the mistakes.

---

## Week 6 Summary (MM/DD/YYYY)
### This week I worked on:

[Your answer here]

### This week I learned:

[Your answer here]

### My successes this week were:

[Your answer here]

### The challenges I faced this week were:

[Your answer here]

---

## Week 7 Summary (MM/DD/YYYY)
### This week I worked on:

[Your answer here]

### This week I learned:

[Your answer here]

### My successes this week were:

[Your answer here]

### The challenges I faced this week were:

[Your answer here]

---

## Week 8 Summary (MM/DD/YYYY)
### This week I worked on:

[Your answer here]

### This week I learned:

[Your answer here]

### My successes this week were:

[Your answer here]

### The challenges I faced this week were:

[Your answer here]

---

## Week 9 Summary (MM/DD/YYYY)
### This week I worked on:

[Your answer here]

### This week I learned:

[Your answer here]

### My successes this week were:

[Your answer here]

### The challenges I faced this week were:

[Your answer here]

---

## Week 10 Summary (MM/DD/YYYY)
### This week I worked on:

[Your answer here]

### This week I learned:

[Your answer here]

### My successes this week were:

[Your answer here]

### The challenges I faced this week were:

[Your answer here]

---

## Week 11 Summary (MM/DD/YYYY)
### This week I worked on:

[Your answer here]

### This week I learned:

[Your answer here]

### My successes this week were:

[Your answer here]

### The challenges I faced this week were:

[Your answer here]

---

## Week 12 Summary (MM/DD/YYYY)
### This week I worked on:

[Your answer here]

### This week I learned:

[Your answer here]

### My successes this week were:

[Your answer here]

### The challenges I faced this week were:

[Your answer here]

---

## Week 13 Summary (MM/DD/YYYY)
### This week I worked on:

[Your answer here]

### This week I learned:

[Your answer here]

### My successes this week were:

[Your answer here]

### The challenges I faced this week were:

[Your answer here]

---