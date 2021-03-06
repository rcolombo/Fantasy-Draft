#!/usr/bin/env python
import sqlite3
from mechanize import Browser
from BeautifulSoup import BeautifulSoup
import os

def main():
    url = 'http://football.fantasysports.yahoo.com/f1/87516/players'
    mech = Browser()
    mech.open(url)
    try:
        mech.select_form(nr=0)
        mech['login'] = os.environ['YMAIL']
        mech['passwd'] = os.environ['YPASS']
        r = mech.submit().read()
        soup = BeautifulSoup(r)
    except Exception:
        soup = mech.open(url)

    connection = sqlite3.connect('players.db')
    cursor = connection.cursor()
    cursor.execute('DELETE FROM players')
    cursor.execute('DELETE FROM skill_pos_stats')
    cursor.execute('DELETE FROM kicker_stats')
    cursor.execute('DELETE FROM defense_stats')
    connection.commit()
    # Scrape Non-Kickers
    print "Scraping Position Players..."
    scrape_and_insert(mech, soup, False)
    
    # Scrape Kickers
    print "Scraping Kickers..."
    mech.select_form(nr=2)
    mech['pos'] = ['K',]
    soup = BeautifulSoup(mech.submit().read())
    scrape_and_insert(mech, soup, False)

    # Scrape Defenses and Bye Weeks
    print "Scraping Defenses..."
    mech.select_form(nr=2)
    mech['pos'] = ['DEF',]
    soup = BeautifulSoup(mech.submit().read())
    scrape_and_insert(mech, soup, True)

def scrape_and_insert(mech, soup, defense_bool):
    has_next = True
    while has_next:
        tbl = soup.find("table", {"id": "statTable0"})
        rows = tbl.findAll('tr')
        for row in rows[2:]:
            name = row.find('a', {"class" : "name"}).text
            team, pos = row.find("div", {"class" : "detail"}).text.split(' - ')
            team = team[team.find('(') + 1:]
            pos = pos[:pos.find(')')]
            rank = row.find("td", {"class": "stat wide sorted"}).text
            connection = sqlite3.connect('players.db')
            cursor = connection.cursor()
            if pos in ("QB", "WR", "TE", "RB"):
                stats = row.findAll("td", {"class": "stat"})
                pass_yards = stats[0].text
                pass_td = stats[1].text
                pass_int = stats[2].text
                rush_yards = stats[3].text
                rush_td = stats[4].text
                receptions = stats[5].text
                rec_yards = stats[6].text
                rec_td = stats[7].text
                fumbles = stats[10].text
                cursor.execute('INSERT INTO skill_pos_stats (rank, name, pass_yards, pass_td, pass_int, rush_yards, rush_td, receptions, rec_yards, rec_td, fumbles) \
                                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                    (rank, name, pass_yards, pass_td, pass_int, rush_yards, rush_td, receptions, rec_yards, rec_td, fumbles))
            if pos == "K":
                stats = row.findAll("td", {"class": "stat"})
                t1 = stats[0].text
                t2 = stats[1].text
                t3 = stats[2].text
                t4 = stats[3].text
                t5 = stats[4].text
                pat = stats[5].text
                cursor.execute('INSERT INTO kicker_stats (rank, name, t1, t2, t3, t4, t5, pat) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                    (rank, name, t1, t2, t3, t4, t5, pat))

            if pos == "DEF":
                stats = row.findAll("td", {"class": "stat"})
                points = stats[0].text
                sacks = stats[1].text[:-2]
                safeties = stats[2].text
                interceptions = stats[3].text
                fumble_recoveries = stats[4].text
                td = stats[5].text
                cursor.execute('INSERT INTO defense_stats (rank, name, points, sacks, safeties, interceptions, fumble_recoveries, td) \
                                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                    (rank, name, points, sacks, safeties, interceptions, fumble_recoveries, td))
            cursor.execute('INSERT INTO players (rank, name, team, position) VALUES(?, ?, ?, ?)',
                                (rank, name, team, pos))
            connection.commit()
        link = None
        for l in mech.links(text_regex='Next 25'):
            link = l
        if link:
            mech.follow_link(link)
            soup = BeautifulSoup(mech.response().read())
        else:
            has_next = False
        
    # Filter for opponents to get bye week
    if defense_bool:
        print "Scraping Bye Weeks..."
        mech.select_form(nr=2)
        mech['stat1'] = ['O_O',]
        r = mech.submit().read()
        soup = BeautifulSoup(r)
        has_next = True
        while has_next:
            tbl = soup.find("table", {"id": "statTable0"})
            rows = tbl.findAll('tr')
            for row in rows[2:]:
                bye = row.find("td", {"class":"stat"}).text
                team = row.find("div", {"class" : "detail"}).text.split(' - ')[0]
                team = team[team.find('(') + 1:]
                connection = sqlite3.connect('players.db')
                cursor = connection.cursor()
                cursor.execute('UPDATE players SET bye=? WHERE team=?', (bye, team))
                connection.commit()
            link = None
            for l in mech.links(text_regex='Next 25'):
                link = l
            if link:
                mech.follow_link(link)
                soup = BeautifulSoup(mech.response().read())
            else:
                has_next = False
if __name__ == "__main__":
    main()
