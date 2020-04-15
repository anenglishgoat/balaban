def fit_counts_model(counts, mins_played):
    ## estimates a hierarchical poisson model for count data
    ## takes as input:
    ##      counts, a numpy array of shape (num_players,) containing the total numbers of actions completed (across all games)
    ##      mins_played, a numpy array of shape (num_players,) containing the total number of minutes each player was observed for
    ## returns:
    ##      sl, a numpy array of shape (6000,N) containing 6000 posterior samples of actions per 90 (N is the number of players in the
    ##      original data frame who have actually played minutes)
    ##      sb, a numpy array of shape (6000,2) containing 6000 posterior samples of the population-level gamma shape parameter &
    ##                                          the population-level mean
    ##      kk, boolean indicating which players have actually played minutes
    import numpy as np
    import pymc3 as pm
    kk = (mins_played > 0) & np.isfinite(counts)
    mins_played = mins_played[kk]
    counts = counts[kk]
    N = counts.shape[0]

    with pm.Model() as model:
        beta = pm.HalfNormal('beta', sigma=100)
        mu = pm.HalfFlat('mu')
        lambdas = pm.Gamma('lambdas', alpha=mu * beta, beta=beta, shape=N)
        lambda_tilde = lambdas * mins_played
        y = pm.Poisson('y', lambda_tilde, observed=counts)
        approx = pm.fit(n=30000)
    sl = approx.sample(6000)['lambdas'] * 90
    sb = np.c_[approx.sample(6000)['beta'], approx.sample(6000)['mu']]
    return [sl, sb, kk, 'count']


def fit_successes_model(successes, attempts):
    ## estimates a hierarchical binomial model for success rate data
    ## takes as input:
    ##      successes, a numpy array of shape (num_players,) containing the total numbers of successful actions (across all games)
    ##      attempts, a numpy array of shape (num_players,) containing the total numbers of attempted actions (across all games)
    ## returns:
    ##      sl, a numpy array of shape (6000,N) containing 6000 posterior samples of success probabilites (N is the number of players in the
    ##      original data frame who have actually attempted a pass)
    ##      sb, a numpy array of shape (6000,2) containing 6000 posterior samples of the population-level beta parameters
    ##      kk, boolean indicating which players have actually attempted a pass
    import numpy as np
    import pymc3 as pm
    import pymc3.distributions.transforms as tr
    import theano.tensor as tt
    kk = (attempts > 0) & np.isfinite(successes)
    attempts = attempts[kk]
    successes = successes[kk]
    N = attempts.shape[0]

    def logp_ab(value):
        ''' prior density'''
        return tt.log(tt.pow(tt.sum(value), -5 / 2))

    with pm.Model() as model:
        # Uninformative prior for alpha and beta
        ab = pm.HalfFlat('ab',
                         shape=2,
                         testval=np.asarray([1., 1.]))
        pm.Potential('p(a, b)', logp_ab(ab))

        lambdas = pm.Beta('lambdas', alpha=ab[0], beta=ab[1], shape=N)

        p = pm.Binomial('y', p=lambdas, observed=successes, n=attempts)
        approx = pm.fit(n=30000)
    sl = approx.sample(6000)['lambdas'] * 100
    sb = approx.sample(6000)['ab']
    return [sl, sb, kk, 'success']


def fit_expected_successes_per_action_model(xS, attempts):
    ## estimates a hierarchical binomial model for success rate data
    ## takes as input:
    ##      sp, a numpy array of shape (num_players,) containing the expected successes per action for each player (e.g. xG per shot, xA per KP)
    ##      attempts, a numpy array of shape (num_players,) containing the total numbers of attempted actions for each player (e.g. shots, key passes)
    ## returns:
    ##      sl, a numpy array of shape (6000,N) containing 6000 posterior samples of success probabilites (N is the number of players in the
    ##      original data frame who have registered non-zero expected succcesses)
    ##      sb, a numpy array of shape (6000,3) containing 6000 posterior samples of: the population-level & observation-level beta 'sample size'
    ##              parameters and the population-level mean
    ##      kk, boolean indicating which players have actually registered non-zero expected successes
    import numpy as np
    import pymc3 as pm
    kk = (attempts > 0) & (xS > 0)
    sp = xS[kk] / attempts[kk]
    attempts = attempts[kk]
    N = attempts.shape[0]

    with pm.Model() as model:
        v = pm.HalfNormal('v', shape=2, sigma=100)
        mu = pm.Uniform('mu')
        lambdas = pm.Beta('lambdas', alpha=mu * v[0], beta=(1 - mu) * v[0], shape=N)
        y = pm.Beta('y',
                    alpha=lambdas * (attempts * (v[1] + 1) - 1),
                    beta=(1 - lambdas) * (attempts * (v[1] + 1) - 1),
                    observed=sp)
        approx = pm.fit(n=30000)
    sl = approx.sample(6000)['lambdas']
    sb = np.c_[approx.sample(6000)['v'], approx.sample(6000)['mu']]
    return [sl, sb, kk, 'expected']


def fit_expected_successes_per90_model(xSuccess_model, attempts_model):
    ## the inputs are two models which should have been returned by:
    ##    fit_expected_successes_per_action_model (first argument)
    ##    fit_counts_model (second argument)
    ## the input models should estimate
    ##    the number of actions attempted per 90 (e.g. shots or key passes) -- fit on count data
    ##    the probability per action that they lead to the corresponding desired outcome (e.g. goal or assist) -- fit on xG/xA data
    kk = (xSuccess_model[2] & attempts_model[2])
    sl = (attempts_model[0][:, kk[attempts_model[2]]] * xSuccess_model[0][:, kk[xSuccess_model[2]]])
    return [sl, [], kk, 'expected_per90']


def fit_adj_pass_model(successes, attempts):
    ## inputs are two lists in the form:
    ##       successes = [successful long passes, total successful passes]
    ##       attempts = [attempted long passes, total attempted passes]
    ## returns:
    ##      sl, a numpy array of shape (6000,N) containing 6000 posterior samples of success probabilites (N is the number of players in the
    ##      original data frame who have registered non-zero expected succcesses)
    ##      sb, an empty list
    ##      kk, boolean indicating which players have actually registered non-zero expected successes
    ##      'adj_pass', character string indicating the model type.
    import numpy as np
    import pymc3 as pm
    import pymc3.distributions.transforms as tr
    import theano.tensor as tt
    LonCmp = successes[0]
    TotCmp = successes[1]
    LonAtt = attempts[0]
    TotAtt = attempts[1]
    kk = (LonCmp > 0) & np.isfinite(LonAtt)
    LonCmp = LonCmp[kk]
    LonAtt = LonAtt[kk]
    TotCmp = TotCmp[kk]
    TotAtt = TotAtt[kk]
    ShCmp = TotCmp - LonCmp
    ShAtt = TotAtt - LonAtt
    average_long_tendency = np.mean(LonAtt / TotAtt)
    N = np.sum(kk)

    def logp_ab(value):
        ''' prior density'''
        return tt.log(tt.pow(tt.sum(value), -5 / 2))

    with pm.Model() as model:
        # Uninformative prior for alpha and beta
        ab_short = pm.HalfFlat('ab_short',
                               shape=2,
                               testval=np.asarray([1., 1.]))
        ab_long = pm.HalfFlat('ab_long',
                              shape=2,
                              testval=np.asarray([1., 1.]))
        pm.Potential('p(a_s, b_s)', logp_ab(ab_short))
        pm.Potential('p(a_l, b_l)', logp_ab(ab_long))

        lambda_short = pm.Beta('lambda_s', alpha=ab_short[0], beta=ab_short[1], shape=N)
        lambda_long = pm.Beta('lambda_l', alpha=ab_long[0], beta=ab_long[1], shape=N)

        y_short = pm.Binomial('y_s', p=lambda_short, observed=ShCmp, n=ShAtt)
        y_long = pm.Binomial('y_l', p=lambda_short * lambda_long, observed=LonCmp, n=LonAtt)
        approx = pm.fit(n=30000)
    s_sh = approx.sample(6000)['lambda_s']
    s_lo = approx.sample(6000)['lambda_l']
    sl = average_long_tendency * s_lo + (1 - average_long_tendency) * s_sh
    return [sl, [], kk, 'adj_pass']


def estimate_model(a, b, model_type):
    if model_type == 'count':
        out = fit_counts_model(a, b)
    elif model_type == 'success_rate':
        out = fit_successes_model(a, b)
    elif model_type == 'xSpA':
        out = fit_expected_successes_per_action_model(a, b)
    elif model_type == 'adj_pass':
        try:
            out = fit_adj_pass_model(a, b)
        except ValueError:
            print(
                "Check inputs. The inputs should be two lists of the form [successful long passes, total successful passes] & [attempted long passes, total attempted passes]")
    elif model_type == 'xSp90':
        try:
            out = fit_expected_successes_per90_model(a, b)
        except ValueError:
            print(
                "Check inputs. The inputs should be two pre-estimated models. The first argument should be a list returned by a 'counts' model. The second argument should be a list returned by an 'xSpA' model.")
    else:
        raise ValueError("Invalid model_type. model_type should be one of 'count', 'success_rate', 'xSpA', or 'xSp90'")
    return out


def obtain_player_quantiles(model, player_index):
    model_type = model[3]
    import numpy as np
    if model_type == 'count':
        from scipy.stats import gamma
        pind = np.arange(np.shape(model[2])[0])[model[2]]
        pind = np.where(pind == player_index)[0]
        percentile_hist = np.histogram(
            gamma.cdf(model[0][:, pind],
                      a=np.mean(model[1][:, 1]) * np.mean(model[1][:, 0]),
                      scale=90 / np.mean(model[1][:, 0])),
            bins=25)
        per90_quantiles = np.quantile(model[0][:, pind], [0.125, 0.5, 0.875])
    elif model_type == 'success':
        from scipy.stats import beta
        pind = np.arange(np.shape(model[2])[0])[model[2]]
        pind = np.where(pind == player_index)[0]
        percentile_hist = np.histogram(
            beta.cdf(model[0][:, pind] / 100,
                     a=np.mean(model[1][:, 0]),
                     b=np.mean(model[1][:, 1])),
            bins=25)
        per90_quantiles = np.quantile(model[0][:, pind], [0.05, 0.5, 0.95])
    elif model_type == 'expected':
        from scipy.stats import beta
        pind = np.arange(np.shape(model[2])[0])[model[2]]
        pind = np.where(pind == player_index)[0]
        percentile_hist = np.histogram(
            beta.cdf(model[0][:, pind],
                     a=np.mean(model[1][:, 2]) * np.mean(model[1][:, 0]),
                     b=(1 - np.mean(model[1][:, 2])) * np.mean(model[1][:, 0])),
            bins=25)
        per90_quantiles = np.quantile(model[0][:, pind], [0.05, 0.5, 0.95])
    elif (model_type == 'expected_per90') | (model_type == 'adj_pass'):
        pind = np.arange(np.shape(model[2])[0])[model[2]]
        pind = np.where(pind == player_index)[0]
        samps_flat = np.random.choice(model[0].flatten(), size=5000)  ## downsample to make cdf quicker to compute
        sorted_samps = np.sort(samps_flat)
        ecdf = lambda x: np.sum(sorted_samps[:, None] < x, axis=0) / len(sorted_samps)
        percentile_hist = np.histogram(
            ecdf(model[0][:, pind].T),
            bins=25)
        per90_quantiles = np.quantile(model[0][:, pind], [0.05, 0.5, 0.95])
    else:
        print("Invalid model type. Must be one of 'count', 'success', 'expected', 'expected_per90' or 'adj_pass'")
    return percentile_hist, per90_quantiles


def get_col_dtype(col):
    import pandas as pd
    import numpy as np
    """
    Infer datatype of a pandas column, process only if the column dtype is object.
    input:   col: a pandas Series representing a df column.
    """

    if col.dtype == "object":

        # try numeric
        try:
            col_new = pd.to_datetime(col.dropna().unique())
            return col_new.dtype
        except:
            try:
                col_new = pd.to_numeric(col.dropna().unique())
                return np.dtype('float64')
            except:
                try:
                    col_new = pd.to_timedelta(col.dropna().unique())
                    return col_new.dtype
                except:
                    return "object"

    else:
        return col.dtype
