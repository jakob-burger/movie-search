# This is a sample Python script.

# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import os
import re
import sys
import threading
import tkinter
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from typing import List

dirname = ""
dir_depth = ""
if getattr(sys, 'frozen', False):
    dirname = os.path.dirname(sys.executable)
    dir_depth = "filmneZuRunterladen"
elif __file__:
    dirname = os.path.dirname(__file__)

if os.name == 'nt':  # if on Windows
    pathToGeckodriver = os.path.join(dirname, dir_depth, "geckodriver.exe")
    dirname = os.path.join(dirname, "..")
else:
    pathToGeckodriver = os.path.join(dirname, dir_depth, "geckodriver")
pathToFilmne = os.path.join(dirname, "Filmne etc.txt")
pathToRunterladen = os.path.join(dirname, "Runterladen.txt")
# pathToGeckodriver = "/home/peter/Schreibtisch/Dropbox/filmneZuRunterladen/geckodriver"
# pathToFilmne = "/home/peter/Schreibtisch/Dropbox/Filmne etc.txt"
# pathToRunterladen = "/home/peter/Schreibtisch/Dropbox/Runterladen.txt"


firstTimeOnPage = False
moviesOnNetflix = []
moviesOnAmazon = []
list_of_movies_which_could_not_be_found = []


def start_thread():
    global driver
    options = Options()
    options.headless = not headless_var.get()
    driver = webdriver.Firefox(options=options, executable_path=pathToGeckodriver)
    thread = threading.Thread(target=check_all_movie_titles)
    thread.setDaemon(True)
    thread.start()
    header_label.config(text="Startup...")
    start_button.config(state="disabled")
    headless_checkbutton.config(state="disabled")



root = tkinter.Tk()
headless_var = tkinter.BooleanVar()
play_sound_var = tkinter.BooleanVar()
frame = tkinter.Frame(root)
header_label = tkinter.Label(root, text="", anchor="w", padx=10, pady=10)
progress_label = tkinter.Label(frame, text="", anchor="w", padx=10, pady=10)
time_progress_label = tkinter.Label(frame, text="", anchor="w", padx=10, pady=10)
start_button = tkinter.Button(root, text="Start", padx=10, command=start_thread)
headless_checkbutton = tkinter.Checkbutton(root, text="Show Window", variable=headless_var)
play_sound_checkbutton = tkinter.Checkbutton(root, text="Play Sound When Finished", variable=play_sound_var)


def check_all_movie_titles():
    try:
        movie_names = get_all_movies()
        number_of_items_to_use_for_time_extrapolation = 10
        number_of_movies = len(movie_names)
        extrapolation_length = number_of_movies/number_of_items_to_use_for_time_extrapolation
        extrapolation_time_calculated = False
        extrapolation_time = ''
        time_progress_label.config(text='Calculating approximate length...')
        start_time = datetime.now().replace(microsecond=0)

        for index, movieName in enumerate(movie_names):
            if index is number_of_items_to_use_for_time_extrapolation:
                end_time = datetime.now().replace(microsecond=0)
                duration_time = (end_time - start_time) * extrapolation_length
                duration_seconds = duration_time.seconds
                duration_time_with_rounded_seconds = timedelta(seconds=duration_seconds)
                extrapolation_time_calculated = True
                extrapolation_time = str(duration_time_with_rounded_seconds)
            check_title(movieName)
            update_progress_bar(number_of_movies, index)
            if extrapolation_time_calculated:
                current_time = datetime.now().replace(microsecond=0)
                elapsed_time = str(current_time - start_time)
                time_progress = "Approximate Length: %s/%s" % (elapsed_time, extrapolation_time)
                time_progress_label.config(text=time_progress)
        write_to_runterladen_file()
        if play_sound_var.get():
            print('\007')  # do the finished sound

    except Exception as e:
        header_label.config(text="ERROR", bg="red")
        raise type(e)(e.message)

    header_label.config(text="Analyzing finished. Movies have been written to file.", bg="green")



def main():
    tkinter.Label(root, text="Filmne ===> Runterladen", font=('Arial', 20), padx=10, pady=10).grid(row=0, column=0)

    headless_checkbutton.grid(row=1, column=0)
    play_sound_checkbutton.grid(row=2, column=0)
    start_button.grid(row=3, column=0)

    frame.grid(row=5, column=0)
    header_label.grid(row=4, column=0)
    progress_label.grid(row=1, column=0)
    time_progress_label.grid(row=1, column=1)

    tkinter.Label(root,
                  text="Note: Results will only be written to Runterladen.txt after all movies have been analyzed.",
                  font=('Arial', 7), padx=10, pady=10).grid(row=6, column=0)
    play_sound_checkbutton.select()
    root.mainloop()


def write_to_runterladen_file():
    to_write = ["Netflix:\n"]
    to_write.extend(moviesOnNetflix)
    to_write.append("\n\nAmazon Prime:\n")
    to_write.extend(moviesOnAmazon)
    to_write.append("\n\nUnauffindbar:\n")
    to_write.extend(list_of_movies_which_could_not_be_found)

    runterladen = open(pathToRunterladen, "w", encoding='cp1252')
    for line in to_write:
        runterladen.write(line + "\n")


def update_progress_bar(nr_of_all_movies: int, nr_of_current_movie: int):
    header_label.config(text="Analysing...")
    progress = "Analyzing Movie: %s/%s" % (str(nr_of_current_movie + 1), str(nr_of_all_movies))
    progress_label.config(text=progress)
    pass


def get_all_movies():
    filmne = open(pathToFilmne, encoding='cp1252')
    filmne_string_list = filmne.readlines()
    filmne_string_list = [x.strip() for x in filmne_string_list]  # Remove all \n
    filmne_string_list = list(filter(None, filmne_string_list))  # Remove all empty strings from list
    filmne_string_list.remove("Filme:")
    filmne_string_list = remove_all_non_movies(filmne_string_list)
    filmne_string_list = remove_all_comments(filmne_string_list)
    filmne_string_list = [s.rstrip() for s in filmne_string_list]  # remove all trailing whitespaces

    return filmne_string_list


def remove_all_non_movies(filmne_string_list: List[str]):
    index = -1
    for filmne_str in filmne_string_list:
        if "___" in filmne_str:
            index = filmne_string_list.index(filmne_str)
            break

    filmne_string_list = filmne_string_list[:index]
    return filmne_string_list


def remove_all_comments(filmne_string_list: List[str]):
    to_return = []
    for filmne_str in filmne_string_list:
        comment = re.search(".*(#.*)", filmne_str)
        if comment is not None:
            str_without_comment = filmne_str.replace(comment.group(1), "")
            to_return.append(str_without_comment)
        else:
            to_return.append(filmne_str)

    return to_return


def check_title(title: str):
    global firstTimeOnPage
    if not firstTimeOnPage:
        driver.get("https://www.werstreamt.es")
        accept_cookies()
        firstTimeOnPage = True

    if navigate_to_movie_page(title):
        if check_for_netflix():
            moviesOnNetflix.append(title)
        if check_for_amazon():
            moviesOnAmazon.append(title)


def check_for_netflix():
    return check_for_provider("netflix")


def check_for_amazon():
    return check_for_provider("amazon")


def check_for_provider(provider_name: str):
    providers = driver.find_elements_by_class_name("provider")

    for provider in providers:
        try:
            provider.find_element_by_id(provider_name)
            # Will throw an exception if this is not the right provider, thereby skipping this provider
            image = provider.find_element_by_tag_name("i")
            style = image.get_attribute("style")
            if "green" in style:
                return True

        except NoSuchElementException:
            pass

    return False


def navigate_to_movie_page(title: str):
    results = List[str]
    had_exception = True
    could_navigate_to_movie_page = True
    try:
        results = search(title)
        if not results:
            list_of_movies_which_could_not_be_found.append(title)
            could_navigate_to_movie_page = False
        else:
            results[0].click()
        had_exception = False
    except TimeoutException:
        had_exception = False
        pass  # If there is only one movie with the given name, werstreamt.es will jump directly to the movie page
    except ElementClickInterceptedException:
        hide_cmpwrapper_if_present()
        results[0].click()
        had_exception = False
    finally:
        if had_exception:
            raise Exception('The Exception occurred while searching for this title: ', title)
        return could_navigate_to_movie_page


def hide_cmpwrapper_if_present():
    try:
        cmp_wrapper = driver.find_element_by_id('cmpwrapper')
        driver.execute_script("arguments[0].style.visibility='hidden'", cmp_wrapper)
    except NoSuchElementException:
        pass  # There seems to be no element to click on


def search(title: str):
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "NiceSearchForm_SearchForm_q"))
    )
    search_bar = driver.find_element_by_id("NiceSearchForm_SearchForm_q")

    search_bar.clear()
    search_bar.send_keys(title)
    search_bar.send_keys(Keys.RETURN)
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Suche nach »%s« in Liste der Filme und Serien')]" % title))
    )
    movie_year = title.split('(')[1].replace(')', '')
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), ', %s')]" % movie_year))
    )
    results_list = driver.find_elements_by_xpath("//*[contains(text(), ', %s')]" % movie_year)
    return results_list


def accept_cookies():
    try:
        accept_cookies_button = driver.find_element_by_id("cmpwelcomebtnyes")
        accept_cookies_button.click()
    except NoSuchElementException:
        pass  # The cookie button appears to be already clicked


main()
driver.quit()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
