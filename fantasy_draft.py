import wx
import wx.lib.mixins.listctrl as listmix
import sqlite3
import wx.grid as gridlib

class PlayerPage(wx.Panel, listmix.ColumnSorterMixin):
    draft_team_index = 0
    snake_back = False
    # Stores the ranks of drafted players
    drafted = []
    def __init__(self, parent):
        panel = wx.Panel.__init__(self, parent, -1)
        
        # Create a combobox drop down for filtering
        filters = ['All', 'QB', 'WR', 'RB', 'TE', 'Flex', 'K', 'DEF']
        wx.StaticText(self, -1, "Filter By Positions:", pos=(10, 7))
        self.combo_box = wx.ComboBox(self, pos=(140,0), choices=filters, style=wx.CB_DROPDOWN
                                                                                | wx.TE_PROCESS_ENTER)
        # cals the filter method when an option is selected
        self.combo_box.Bind(wx.EVT_COMBOBOX, self.filter_p)

        # Create a listctrl for holding the players
        self.list_ctrl = wx.ListCtrl(self, pos=(10,30), size=(450,650), style=wx.LC_REPORT
                                                                             |wx.BORDER_SUNKEN)
        # Create proper column headers for listctrl
        self.list_ctrl.InsertColumn(0, 'Yahoo! Rank')
        self.list_ctrl.InsertColumn(1, 'Player Name')
        self.list_ctrl.InsertColumn(2, 'Position')
        self.list_ctrl.InsertColumn(3, 'Team')
        self.list_ctrl.InsertColumn(4, 'Bye Week')
        
        # Create a listctrl for storing the teams in the league
        self.teams = wx.ListCtrl(self, pos=(480,40), size=(225,275), style=wx.LC_REPORT
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
    
    def draft(self, event):
        idx = self.list_ctrl.GetFirstSelected(self)
        rank = self.list_ctrl.GetItem(idx, 0).GetText()
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

class DraftPositionRandomizer(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

class BigBoard(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        t = wx.StaticText(self, -1, "Big Board goes here", (40,40))
        bigboard = gridlib.Grid(self)
        bigboard.CreateGrid(14, 12)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(bigboard, 1, wx.EXPAND)
        self.SetSizer(sizer)

class TeamPage(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        t = wx.StaticText(self, -1, "Teams and drafted players go here", (60,60))

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="2012 Fantasy Football Draft", size=(900,750))

        # Here we create a panel and a notebook on the panel
        p = wx.Panel(self)
        nb = wx.Notebook(p)

        # Create the page windows as children of the notebook
        players = PlayerPage(nb)
        randomizer = DraftPositionRandomizer(nb)
        bigboard = BigBoard(nb)

        # Add the pages to the notebook with the label to show on the tab
        nb.AddPage(players, "Undrafted Players")
        nb.AddPage(randomizer, "Draft Position Randomizer")
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
