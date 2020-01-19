class bosko:
    def __init__(self, df, league_season_string):
        self.df = df
        self.league_season_string = league_season_string
        self.models = []
        self.labels = []
        
    def add_model(self,a,b,type,name):
        from balaban.utils import estimate_model
        import numpy as np
        if isinstance(a, str):
            a = self.df[a]
        if isinstance(b, str):
            b = self.df[b]
        a = np.array(a)
        b = np.array(b)
        new_model = estimate_model(a,b,type)
        self.models.append(new_model)
        self.labels.append(name)

    def delete_model(self,name):
        import numpy as np
        which_mod = np.min(np.where(self.labels == name)[0])
        del self.models[which_mod]
        del self.labels[which_mod]
    def get_model(self,name):
        import numpy as np
        which_mod = np.min(np.where(self.labels == name)[0])
        return self.models[which_mod]
        
    def make_plot(self,player_query,use_pretty_font=True,dpi = 125):
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
        import matplotlib
        import numpy as np
        import os
        from balaban.utils import obtain_player_quantiles
        from importlib_resources import path as get_font_path
        if use_pretty_font:
            font_path = get_font_path('balaban','JosefinSans-Regular.ttf')
            try:
                with font_path as f:
                  fname = str(f)
                  fp_title = fm.FontProperties(fname=fname,size = 10)
                  fp_subtitle = fm.FontProperties(fname=fname,size = 9)
                  fp_labels = fm.FontProperties(fname=fname,size = 8)
                  fp_medians = fm.FontProperties(fname=fname,size = 7)
            except:
                fp_title = fm.FontProperties(size = 10)
                fp_subtitle = fm.FontProperties(size = 9)
                fp_labels = fm.FontProperties(size = 8)
                fp_medians = fm.FontProperties(size = 7)
        else:
              fp_title = fm.FontProperties(size = 10)
              fp_subtitle = fm.FontProperties(size = 9)
              fp_labels = fm.FontProperties(size = 8)
              fp_medians = fm.FontProperties(size = 7)
                
        player_list = np.array(self.df['Player'])
        team_list = np.array(self.df['Squad'])
        mins_played = np.array(self.df['Minutes'])
        models = self.models
        labels = self.labels

        pl = np.where(player_list == player_query)[0][0]
        n_bars = len(models)
        fig = plt.figure(dpi = dpi)
        ax = plt.subplot(111,projection = 'polar')
        p90_collected = [None] * n_bars
        for j in range(n_bars):
          h,p90 = obtain_player_quantiles(models[j],pl)
          p90_collected[j] = p90
          ax.bar(np.pi / 2 + j * 2 * np.pi /n_bars,
                 1,
                 color = 'white',
                 edgecolor = 'seagreen',
                 width = 2 * np.pi / n_bars,
                 linewidth = 0.2)
          for i in range(1,25):
            ax.bar(np.pi / 2 + j * 2 * np.pi /n_bars,
                   h[1][i]-h[1][i-1],
                   alpha = h[0][i] / np.max(h[0]),
                   color = 'seagreen',
                   width = 2 * np.pi / n_bars,
                   bottom = h[1][i-1])

        ax.axis('off')
        for quantile in [0.25,0.5,0.75]:
          ax.plot(np.linspace(0,2 * np.pi,200),quantile * np.ones(200),c = 'gray', alpha = 0.2 + 0.3 * (quantile == 0.5),ls = '--')
        ax.plot(np.linspace(0,2 * np.pi,200),np.ones(200),c = 'gray', alpha = 0.5)

        fig.suptitle(player_list[pl] + ' (' + team_list[pl] + '), ' + self.league_season_string,y=1.04,fontsize = 10,fontproperties=fp_title)
        tit = ax.set_title('Passing metrics; 90s played: ' + str(mins_played[pl] / 90), fontsize = 9, y = 1.1,fontproperties=fp_subtitle)
        theta = np.pi / 2 + np.arange(n_bars) * 2 * np.pi /n_bars
        theta_lower = np.pi / 2 + np.arange(n_bars) * 2 * np.pi /n_bars + np.pi / 20
        rotations = np.rad2deg(theta) - 90 - 180 * ((theta > np.pi) & (theta < 2 * np.pi))
        rotations_lower = np.rad2deg(theta_lower) - 90 - 180 * ((theta_lower > np.pi) & (theta_lower < 2 * np.pi))


        for idx in range(n_bars):
            lab = ax.text(theta[idx], 1.2 , labels[idx], 
                     ha='center', 
                     va='center', 
                     rotation=rotations[idx], 
                     rotation_mode="anchor",
                     fontsize = 8,
                     fontproperties=fp_labels,)
            lab = ax.text(theta[idx], 1.075 , f'{p90_collected[idx][1]:.3}' + ' (' + f'{p90_collected[idx][0]:.3}' + ', ' + f'{p90_collected[idx][2]:.3}' + ')', 
                     ha='center', 
                     va='center', 
                     rotation=rotations[idx], 
                     rotation_mode="anchor",
                     fontsize = 9,
                     fontproperties=fp_medians,
                     color = 'firebrick')
        plt.show()
