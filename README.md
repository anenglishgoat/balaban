# balaban
The basic goal of `balaban` is to improve the modelling of uncertainty in common player-level metrics (e.g., pass completion percentages, 
goals per 90, xG per shot, xA per 90). This is done through Bayesian hierarchical models for the 4 most common types of metric:
  1. Absolute counts per 90 (passes, shots, assists, goals, tackles etc.)
  2. Success rates (pass completion, tackle success, shots on target etc.)
  3. Model-derived 'expected' successes per action (xA per key pass, xG per shot)
  4. Model-derived 'expected' successes per 90 (xA, xG)
  
If you have suggestions for other models you'd like to see, please let me know via [Twitter](https://twitter.com/AnEnglishGoat).

Here's an [example notebook](https://colab.research.google.com/drive/1CRybRbZXe3Y6AkPh__7jaKCF9O2EaSa6#offline=true&sandboxMode=true).

**TODO:**

   * ~~There appears to be a way of scraping with Selenium. This is great news and I'll write a function that just requires the league name to pull the latest data from fbref so users don't have to worry about downloading and formatting csv files.~~ This is done now. See the section on [Data Preparation](#data-preparation) below.
   * A few of the models are conjugate (don't require MCMC as they can be computed analytically) so I will write much faster sampling functions for those when I've got some time.
   * Something that will take more time is turning this thing into a Heroku web app. I really want it to be easy to produce the radar for any given player. I also want fans/analysts to acknowledge that quite often you can't really say much about how good a player is at a particular thing via these sort of stats. *When you can't, it's good to know that you can't.* 

**What does this get me?**

The ultimate output is a radar-like plot of the model estimates for various metrics. The intensity of green represents our certainty
about the players *percentile rank* for the given metric, taking into account sample size and the inherent variability of the metric.

![alt text](https://i.imgur.com/JlQadAq.png "Mikel Merino")

Darker greens mean we're more confident in that value, so we're fairly sure that Merino's 'true' passing success rate is around the league
median for midfielders. We're also fairly sure that he ranks pretty highly (somewhere around the 85th percentile) for successful passes 
into the final 3rd per 90. However, because assists are pretty rare and Merino hasn't done anything particularly spectacular, we're not
very certain about his xA rankings, despite him having played a decent number of games. He's not particularly special and he's unlikely
to be in the top 50% of expected assisters but, aside from that, we can't say much. It's important to remember that 'sample size'
isn't just about the number of minutes played.

The red numbers are the median and 90% credible intervals for the actual value we're trying to estimate (e.g., successful balls into the 
penalty area per 90). Essentially, we're 90% sure his true value lies between the two numbers in the brackets.


**Who cares?**

Probably not many people, but when assessing a player I think it's useful to have:
  * A reasonable estimate of the uncertainty associated with each metric (due to sample sizes, the general variability of the metric)
  * A reasonable estimate of the uncertainty associated with where players *rank* on each metric (i.e., their percentiles)
  * The use of prior information to temper crazy estimates from small sample sizes (you're average until you sufficiently prove otherwise)
 
**Why hierarchical modelling?**

It gets us all three of the things I mentioned above in a principled way. The 'hierarchical' part of the name comes from the fact that 
there are two levels to the model: the population level and the individual level. The idea is that we can use the data from *everybody* in the 
population (say all midfielders in La Liga) to give us an idea about what a reasonable estimate looks like. As an example, if a guy has played 
180 minutes and registered a pass completion percentage of 31%, we can use the information in the rest of the data to infer that he probably isn't *that* bad
because there is practically nobody with a decent sample size who has that sort of pass completion level. However, we have learned a little
bit about this player. We know he's probably not a *really* good passer, because a really good passer wouldn't be putting up such bad numbers
even over a small number of passes. This is the tradeoff in hierarchical modelling. The resulting estimate, rather than just being a '31%' without
much context, would be quite a wide distribution covering the lower portion of the population.


## **How can I use it?**

You can install via `pip install balaban`.

You can install by cloning this repo: `git clone https://github.com/anenglishgoat/balaban`

Or you can modify this [Colab notebook](https://colab.research.google.com/drive/1CRybRbZXe3Y6AkPh__7jaKCF9O2EaSa6#offline=true&sandboxMode=true) by signing in with your Google account.

Here is the usage pipeline:

### **Data preparation**

You have a few options:

#### **Either**:

Generate a `.csv` file containing the data you want to include. You can download these directly from the 'Squad & Player Stats' tabs on the fbref competition pages, like the one for the [Premier League](https://fbref.com/en/comps/9/Premier-League-Stats). I had  to modify the downloaded `.xls` file a little bit in Excel before saving it as a `.csv`. 

<img src="https://i.imgur.com/cWWjryd.png" width="500"/>

I just removed the additional row at the top (which contained extra labels about pass types) and changed the file type to `.csv`.

Once that's done, you can just pass the filepath of the `.csv` to `balaban.bosko`.
 
#### **Or**:

You can scrape from fbref -- to do so you will need to have downloaded the appropriate `chromedriver.exe` file from [here](https://sites.google.com/a/chromium.org/chromedriver/downloads) and made a note of the filepath. You can then run
```
from balaban import scrape_top_five_leagues
df = scrape_top_five_leagues('path/to/chromedriver.exe', league_names)
```
`league_names` is a list that defaults to `['epl', 'laliga', 'bundesliga', 'ligue1', 'seriea']`, but you can pass any subset of those to reduce the time it takes to scrape.

#### **Or**:

Use a pandas dataframe you've generated another way. Just make sure it has columns called 'Player' (player names; *strings*), 'Squad' (team names; *strings*), 'Pos' (playing positions; *strings*; as per fbref, these are one of `DF`, `MF`, `FW`. They can be combined like `MF,FW`), '90s' (number of 90s played, *float*). 

### **Setting up a bosko object**

```
import balaban
bos = balaban.bosko(df, league_season_string, query_position)
```

This makes a Croatian striker/Python class containing your data that we'll add fitted models to later on.

  * `df` is either a pandas dataframe, a filepath to your csv file,
  or a url to your csv file. As long as either your csv file or dataframe have the columns 'Player', 'Squad', 'Pos' & '90s, you're all good.
  * `league_season_string` is a character string for plotting purposes. It goes where "La Liga, 2019/20" is in the Merino example above.
  * `query_position` is an (optional) character string defining a position filter. For example, if it's `'MF'`, the models will only be fitted on players
  for which the string `'MF'` appears in the Pos column.
    
### **Adding models**

The following function call estimates a model:
```
bos.add_model(a,b,model_type,model_name)
```
*Note*: the first time you try to add a model, there might be a delay of a couple of minutes. That's pyMC3 being installed and compiling some stuff.

`model_type` specifies which of the four possible models will be estimated. The options are
  * `'count'`
    - estimate a hierarchical Poisson model. Suitable for 'count per 90' type metrics.
    - if `model_type == 'count'`, `a` is the total number of observed actions (goals, passes, etc.)
    - if `model_type == 'count'`, `b` is the total number of minutes played
  * `'success_rate'`
    - estimate a hierarchical Binomial model. Suitable for success rate metrics.
    - if `model_type == 'success_rate'`, `a` is the total number of *successful* actions (goals, completed passes, etc.)
    - if `model_type == 'success_rate'`, `b` is the total number of *attempted* actions (shots, attempted passes, etc.)
  * `'xSpA'`
    - estimate a hierarchical Beta model. Suitable for expected success metrics per required action.
    - if `model_type == 'xSpA'`, `a` is the total expected successful actions (e.g., xA, xG)
    - if `model_type == 'xSpA'`, `b` is the total number of *attempted* corresponding actions (e.g., key passes, shots)
  * `'xSp90'`
    - combine a count model and an xSpA model to obtain expected successes per 90
    - if `model_type == 'xSp90'`, `a` is a *previously estimated* xSpA model
    - if `model_type == 'xSp90'`, `b` is a *previously estimated* count model
    - previously estimated models can be retrieved via `bos.get_model(name)`. For example, to estimate an xG90 model:
    
    ```
    bos.add_model('Sh', 'Minutes', 'count', 'Shots/90')
    bos.add_model('xG', 'Sh', 'xSpA', 'xG/Shot')
    bos.add_model(bos.get_model('xG/Shot'), bos.get_model('Shots/90'), 'xSp90', 'xG/90')
    ```
  * `'adj_pass'`
    - estimate a length-adjusted pass completion model. It combines two hierarchical binomial models for passes longer than 25 yards and passes shorter than 25 yards. Essentially a very simple expected passing model.
    - the estimates are the overall passing success rates if the proportion of long passes is set to the average among the cohort. i.e. it adjusts the pass success rate so that everybody has the same long:short pass ratio -- if you're playing mostly long balls, your pass success will naturally be low. This model attempts to correct for that. 
    - if `model_type == 'adj_pass'`, `a` is a list of the form `[successful long passes, total successful passes]`
    - if `model_type == 'adj_pass'`, `b` is a list of the form `[attempted long passes, total attempted passes]`
    
    
`model_name` is also the character string that will be used as a label on any subsequent plots.

`a` and `b` can be either:
  * character strings referring to columns in your input `.csv` or pandas dataframe
  * arrays containing the values themselves (this allows you to use sums of columns or data not in the original csv/data frame)
  
### **Plot the results**

Once all of the models you're interested in have been estimated, you can plot the results using
```
bos.make_plot(query_player,subtit_text,model_names,use_pretty_font)
```
  * `query_player` is a character string
  * `subtit_text` is a character string defining the first part of the plot subtitle. It goes where 'Passing metrics' appears on the Merino plot.
  * `model_names` is an (optional) list of models to plot. Defaults to all of them.
  * `use_pretty_font` is an (optional) Boolean telling me whether you want to use the nice font in the example above (`True`) or
  the matplotlib default font (`False`). Defaults to `True`.
