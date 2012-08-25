import wx
import wx.lib.mixins.listctrl as listmix
import sqlite3
import wx.grid as gridlib
import os.path

class EditableListCtrl(wx.ListCtrl, listmix.TextEditMixin):
    ''' TextEditMixin allows any column to be edited. '''
    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.TextEditMixin.__init__(self)

class PlayerPage(wx.Panel, listmix.ColumnSorterMixin):
    draft_team_index = 0
    snake_back = False
    # Stores the ranks of drafted players
    drafted = []
    def __init__(self, parent, bigboard):

        panel = wx.Panel.__init__(self, parent, -1)
        self.bigboard = bigboard
 
        # Create a text box for filtering players
        wx.StaticText(self, -1, "Filter By Name:", pos=(10,30))
        self.filter_box = wx.TextCtrl(self, pos=(120, 30), size=(150,20))
        self.filter_box.Bind(wx.EVT_TEXT, self.filter_by_text)

        # Create a window for storing pictures
        self.pic_window = wx.Window(self, pos=(475, 350), size=(2000, 400))
        self.player_picture = None
        
        # Create a window for displaying 2011 stats
        self.stats_window = wx.Window(self, pos=(735,40), size=(500,500))

        # Create a combobox drop down for filtering
        filters = ['All', 'QB', 'WR', 'RB', 'TE', 'Flex', 'K', 'DEF']
        wx.StaticText(self, -1, "Filter By Positions:", pos=(10, 7))
        self.combo_box = wx.ComboBox(self, pos=(140,0), choices=filters, style=wx.CB_DROPDOWN
                                                                                | wx.TE_PROCESS_ENTER)
        # cals the filter method when an option is selected
        self.combo_box.Bind(wx.EVT_COMBOBOX, self.filter_p)

        # Create a listctrl for holding the players
        self.list_ctrl = wx.ListCtrl(self, pos=(10,55), size=(450,650), style=wx.LC_REPORT
                                                                             |wx.BORDER_SUNKEN)

        # Create proper column headers for listctrl
        self.list_ctrl.InsertColumn(0, 'Yahoo! Rank')
        self.list_ctrl.InsertColumn(1, 'Player Name')
        self.list_ctrl.InsertColumn(2, 'Position')
        self.list_ctrl.InsertColumn(3, 'Team')
        self.list_ctrl.InsertColumn(4, 'Bye Week')
        
        # Bind clicking on a player to the place_pic function
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.place_picture)

        # Create a listctrl for storing the teams in the league
        self.teams = EditableListCtrl(self, pos=(480,40), size=(225,275), style=wx.LC_REPORT
                                                                             |wx.BORDER_SUNKEN)
        self.teams.InsertColumn(0, 'Draft Position')
        self.teams.InsertColumn(1, 'Team Name') 
        # Not sure what this is doing, educate yourself
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.list_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.teams, 0, wx.ALL | wx.EXPAND, 5)
        parent.SetSizer(sizer)
        
        # Create two buttons for drafting players
        btn = wx.Button(self, pos=(480, 10), size=(225,225), label="Draft Player")
        btn2 = wx.Button(self, pos=(480, 325), size=(225,225), label="Draft Player")
        btn.Bind(wx.EVT_BUTTON, self.draft)
        btn2.Bind(wx.EVT_BUTTON, self.draft)
        
        # Populate the players listctrl
        self.index = 0
        connection = sqlite3.connect('players.db')
        cursor = connection.cursor()
        cursor.execute('select rank, name, position, team, bye from players order by rank asc')
        for result in cursor.fetchall():
            result = map(str, result)
            self.list_ctrl.InsertStringItem(self.index, result[0])
            self.list_ctrl.SetStringItem(self.index, 1, result[1])
            self.list_ctrl.SetStringItem(self.index, 2, result[2])
            self.list_ctrl.SetStringItem(self.index, 3, result[3])
            self.list_ctrl.SetStringItem(self.index, 4, result[4])
            self.index += 1

        
        # Placeholders for teamlistctrl
        for x in range(1,13):
            self.teams.InsertStringItem(x-1, str(x))
            self.teams.SetStringItem(x-1, 1, "Team Name Here")
        
        self.teams.SetItemBackgroundColour(self.draft_team_index, "yellow")
   
    def place_picture(self, event):
        idx = self.list_ctrl.GetFirstSelected(self)
        self.place_stats(idx)
        name = self.list_ctrl.GetItem(idx, 1).GetText().replace(" ", "_")
        team = self.list_ctrl.GetItem(idx, 3).GetText()
        if name == "Steve_Smith" and team == "StL":
            imageFile = './images/Steve_Smith_StL.jpeg'
        elif name == "New_York" and team == "NYJ":
            imageFile = './images/New_York_jets.jpeg'
        else:
            imageFile = './images/%s.jpeg' %(name)
        if os.path.isfile(imageFile):
            if self.player_picture:
                self.player_picture.Destroy()
            jpg1 = wx.Image(imageFile, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
            self.player_picture = wx.StaticBitmap(self.pic_window, -1, jpg1, (0,0), (jpg1.GetWidth(), jpg1.GetHeight()))
            #self.player_picture = wx.StaticBitmap(self.pic_window, -1, jpg1, (10 + jpg1.GetWidth(), 5), (jpg1.GetWidth(), jpg1.GetHeight()))
        else:
            if self.player_picture:
                self.player_picture.Destroy()
    
    def place_stats(self, idx):
        self.stats_window.Destroy()
        self.stats_window = wx.Window(self, pos=(735,40), size=(500,500))
        rank = self.list_ctrl.GetItem(idx, 0).GetText()
        name = self.list_ctrl.GetItem(idx, 1).GetText()
        pos = self.list_ctrl.GetItem(idx, 2).GetText()
        headline = wx.StaticText(self.stats_window, -1, label="2011 Stats                           _")
        headline_font = wx.Font(30, wx.DECORATIVE, wx.NORMAL, wx.BOLD, underline=True)
        headline.SetForegroundColour((165, 42, 42))
        headline.SetFont(headline_font)
        connection = sqlite3.connect('players.db')
        cursor = connection.cursor()
        if pos == "QB":
            cursor.execute('SELECT pass_yards, pass_td, pass_int, rush_yards, rush_td \
                            FROM skill_pos_stats WHERE rank = ?', (rank,))
            stats = cursor.fetchall()[0]
            stat_label_font = wx.Font(20, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
            wx.StaticText(self.stats_window, -1, pos=(0, 35), label="Passing Yards:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 65), label="Passing Touchdowns:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 95), label="Interceptions:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 125), label="Rushing Yards:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 155), label="Rushing Touchdowns:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 35), label="%s" %(stats[0])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 65), label="%s" %(stats[1])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 95), label="%s" %(stats[2])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 125), label="%s" %(stats[3])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 155), label="%s" %(stats[4])).SetFont(stat_label_font)
        if pos == "RB":
            cursor.execute('SELECT rush_yards, rush_td, receptions, rec_yards, rec_td, fumbles \
                            FROM skill_pos_stats WHERE rank = ?', (rank,))
            stats = cursor.fetchall()[0]
            stat_label_font = wx.Font(20, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
            wx.StaticText(self.stats_window, -1, pos=(0, 35), label="Rushing Yards:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 65), label="Rushing Touchdowns:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 95), label="Receptions:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 125), label="Receiving Yards:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 155), label="Receiving Touchdowns:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 185), label="Fumbles:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 35), label="%s" %(stats[0])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 65), label="%s" %(stats[1])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 95), label="%s" %(stats[2])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 125), label="%s" %(stats[3])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 155), label="%s" %(stats[4])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 185), label="%s" %(stats[5])).SetFont(stat_label_font)
        if pos == "WR" or pos == "TE":
            cursor.execute('SELECT receptions, rec_yards, rec_td, fumbles \
                            FROM skill_pos_stats WHERE rank = ?', (rank,))
            stats = cursor.fetchall()[0]
            stat_label_font = wx.Font(20, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
            wx.StaticText(self.stats_window, -1, pos=(0, 35), label="Receptions:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 65), label="Receiving Yards:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 95), label="Receiving Touchdowns:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 125), label="Fumbles:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 35), label="%s" %(stats[0])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 65), label="%s" %(stats[1])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 95), label="%s" %(stats[2])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 125), label="%s" %(stats[3])).SetFont(stat_label_font)
        if pos == "K":
            cursor.execute('SELECT t1, t2, t3, t4, t5, pat\
                            FROM kicker_stats WHERE rank = ?', (rank,))
            stats = cursor.fetchall()[0]
            stat_label_font = wx.Font(20, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
            wx.StaticText(self.stats_window, -1, pos=(0, 35), label="0-19 Yards:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 65), label="20-29 Yards:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 95), label="30-39 Yards:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 125), label="40-49 Yards:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 155), label="50+ Yards:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 185), label="PATs:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 35), label="%s" %(stats[0])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 65), label="%s" %(stats[1])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 95), label="%s" %(stats[2])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 125), label="%s" %(stats[3])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 155), label="%s" %(stats[4])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 185), label="%s" %(stats[5])).SetFont(stat_label_font)
        if pos == "DEF":
            cursor.execute('SELECT points, sacks, safeties, interceptions, fumble_recoveries, td \
                            FROM defense_stats WHERE rank = ?', (rank,))
            stats = cursor.fetchall()[0]
            stat_label_font = wx.Font(20, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
            wx.StaticText(self.stats_window, -1, pos=(0, 35), label="Points Allowed:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 65), label="Sacks:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 95), label="Safeties:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 125), label="Interceptions:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 155), label="Fumble Recoveries:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(0, 185), label="Touchdowns:").SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 35), label="%s" %(stats[0])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 65), label="%s" %(stats[1])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 95), label="%s" %(stats[2])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 125), label="%s" %(stats[3])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 155), label="%s" %(stats[4])).SetFont(stat_label_font)
            wx.StaticText(self.stats_window, -1, pos=(250, 185), label="%s" %(stats[5])).SetFont(stat_label_font)

    def draft(self, event):
        idx = self.list_ctrl.GetFirstSelected(self)
        rank = self.list_ctrl.GetItem(idx, 0).GetText()
        pos = self.list_ctrl.GetItem(idx, 2).GetText()
        name = self.list_ctrl.GetItem(idx, 1).GetText()
        if pos != "DEF":
            name = name.split()[0]+ "\n" + name.split()[1]
        self.drafted.append(rank)
        self.list_ctrl.DeleteItem(idx)
        self.teams.SetItemBackgroundColour(self.draft_team_index, "white")

        if self.snake_back:
            if self.draft_team_index == 0:
                self.snake_back = False
            else:
                self.draft_team_index -=1
        else:
            if self.draft_team_index == 11:
                self.snake_back = True
            else:
                self.draft_team_index += 1
        self.teams.SetItemBackgroundColour(self.draft_team_index, "yellow")
       
        if self.bigboard.colnum + self.bigboard.rownum == 0:
            for x in range(0, 12):
                teamname = self.teams.GetItem(x, 1). GetText()
                self.bigboard.bigboard.SetColLabelValue(x, teamname)
        colors = {"RB": (175, 238, 238), # Light Blue
                  "WR": (124, 252, 0), # Light Green
                  "QB": (250, 128, 114), # Pink
                  "TE": (255, 255, 0), # Yellow
                  "K": (132, 112, 255), # Purple
                  "DEF": (222, 184, 135), # Light Brown
                 }
        self.bigboard.bigboard.SetCellValue(self.bigboard.colnum, self.bigboard.rownum, name)
        self.bigboard.bigboard.SetCellBackgroundColour(self.bigboard.colnum, self.bigboard.rownum, colors[pos])
        self.bigboard.bigboard.SetCellFont(self.bigboard.colnum, self.bigboard.rownum, wx.Font(19, wx.DECORATIVE, wx.BOLD, wx.NORMAL))

        if self.bigboard.colnum % 2 == 0:
            if self.bigboard.rownum < 11:
                self.bigboard.rownum += 1
            else:
                self.bigboard.colnum += 1
        else:
            if self.bigboard.rownum > 0:
                self.bigboard.rownum -= 1
            else:
                self.bigboard.colnum += 1
        
        self.player_picture.Destroy()
        self.stats_window.Destroy()
        self.stats_window = wx.Window(self, pos=(735,40), size=(500,500))

    def filter_p(self, event):
        selection = event.GetString()
        if selection not in ("Flex", "All"):
            sql = "SELECT rank, name, position, team, bye FROM players WHERE position='%s' AND rank NOT IN (%s) ORDER BY rank ASC" %(selection, ','.join(self.drafted))
        elif selection == "All":
            sql = "SELECT rank, name, position, team, bye FROM players WHERE rank NOT IN (%s) ORDER BY rank ASC" %(','.join(self.drafted))
        elif selection == "Flex":
            sql = "SELECT rank, name, position, team, bye FROM players WHERE position IN ('WR', 'RB', 'TE') AND rank NOT IN (%s) ORDER BY rank ASC" %(','.join(self.drafted))

        self.index = 0
        connection = sqlite3.connect('players.db')
        cursor = connection.cursor()
        cursor.execute(sql)
        self.list_ctrl.DeleteAllItems()
        for result in cursor.fetchall():
            result = map(str, result)
            self.list_ctrl.InsertStringItem(self.index, result[0])
            self.list_ctrl.SetStringItem(self.index, 1, result[1])
            self.list_ctrl.SetStringItem(self.index, 2, result[2])
            self.list_ctrl.SetStringItem(self.index, 3, result[3])
            self.list_ctrl.SetStringItem(self.index, 4, result[4])
            self.index += 1

    def filter_by_text(self, event):
        selection = event.GetString()
        player_name = self.filter_box.GetLineText(0)
        sql = "SELECT rank, name, position, team, bye FROM players WHERE name LIKE '%s' AND rank NOT IN (%s) ORDER BY rank ASC" %('%' + selection + '%', ','.join(self.drafted))

        self.index = 0
        connection = sqlite3.connect('players.db')
        cursor = connection.cursor()
        cursor.execute(sql)
        self.list_ctrl.DeleteAllItems()
        for result in cursor.fetchall():
            result = map(str, result)
            self.list_ctrl.InsertStringItem(self.index, result[0])
            self.list_ctrl.SetStringItem(self.index, 1, result[1])
            self.list_ctrl.SetStringItem(self.index, 2, result[2])
            self.list_ctrl.SetStringItem(self.index, 3, result[3])
            self.list_ctrl.SetStringItem(self.index, 4, result[4])
            self.index += 1

class BigBoard(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        t = wx.StaticText(self, -1, "Big Board goes here", (40,40))
        self.bigboard = gridlib.Grid(self)
        self.bigboard.SetDefaultColSize(97)
        self.bigboard.SetDefaultRowSize(39)
        self.bigboard.CreateGrid(16, 12)
        
        self.rownum = 0
        self.colnum = 0
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.bigboard, 1, wx.EXPAND)
        self.SetSizer(sizer)

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="2012 Fantasy Football Draft", size=(900,750))

        # Here we create a panel and a notebook on the panel
        p = wx.Panel(self)
        nb = wx.Notebook(p)

        # Create the page windows as children of the notebook
        bigboard = BigBoard(nb)
        players = PlayerPage(nb, bigboard)

        # Add the pages to the notebook with the label to show on the tab
        nb.AddPage(players, "Undrafted Players")
        nb.AddPage(bigboard, "Big Board")

        # Finally, put the notebook in a sizer for the panel to manage the layout
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)
        p.SetSizer(sizer)

def main():
    app = wx.App(False)
    MainFrame().Show()
    app.MainLoop()    

if __name__ == '__main__':
    main()
