#!/usr/bin/env python3

import json
import requests
import random
import string
import secrets
import time
import re
import collections

try:
    from urllib.parse import parse_qs, urlencode, urlparse
except ImportError:
    from urlparse import parse_qs, urlparse
    from urllib import urlencode

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class HangmanAPI(object):
    def __init__(self, access_token=None, session=None, timeout=None):
        self.hangman_url = self.determine_hangman_url()
        self.access_token = access_token
        self.session = session or requests.Session()
        self.timeout = timeout
        self.guessed_letters = []

        full_dictionary_location = "words_250000_train.txt"
        self.full_dictionary = self.build_dictionary(full_dictionary_location)
        self.ndupdict = []
        for word in self.full_dictionary:
            temp = ""
            for i in range(len(word)):
                if word[i] not in temp:
                    temp += word[i]
            self.ndupdict.append(temp)
        self.full_dictionary_common_letter_sorted = collections.Counter(
            "".join(self.ndupdict)
        ).most_common()

        self.current_dictionary = []
        self.start = 1

    @staticmethod
    def determine_hangman_url():
        links = ["https://trexsim.com", "https://sg.trexsim.com"]

        data = {link: 0 for link in links}

        for link in links:
            requests.get(link)

            for i in range(10):
                s = time.time()
                requests.get(link)
                data[link] = time.time() - s

        link = sorted(data.items(), key=lambda x: x[1])[0][0]
        link += "/trexsim/hangman"
        return link

    def guess(self, word):  # word input example: "_ p p _ e "
        ###############################################
        # Replace with your own "guess" function here #
        ###############################################

        # clean the word so that we strip away the space characters
        # replace "_" with "." as "." indicates any character in regular expressions
        clean_word = word[::2].replace("_", ".")
        clean_word = "^" + clean_word
        clean_word = clean_word + "$"

        # find length of passed word
        len_word = len(clean_word)
        short_dash = len_word
        cnt = 0
        for i in range(len_word - 1):
            if clean_word[i] != ".":
                continue
            cnt += 1
            if clean_word[i] == clean_word[i + 1]:
                continue
            short_dash = min(short_dash, cnt)
            cnt = 0
        if cnt != 0:
            short_dash = min(short_dash, cnt)
            cnt = 0
        if self.start == 1:
            new_dictionary = []
            for word in self.current_dictionary:
                word = "^" + word
                word = word + "$"
                new_dictionary.append(word)
            self.current_dictionary = new_dictionary

        new_dictionary = self.current_dictionary

        # grab current dictionary of possible words from self object, initialize new possible words dictionary to empty
        def _score(a, b):
            return sum([a[i] == b[i] for i in range(min(len(a), len(b)))])

        def best_match(a, b):
            maxi = 0
            _max_score = 0
            for offset in range(len(a)):
                val = pow(7, _score(a[offset:], b)) / (offset + 1)
                if val > _max_score:
                    _max_score = val
                    maxi = offset
            return maxi

        score = {}
        max_onece = 0
        max_word = ""
        for dict_word in new_dictionary:
            shift = best_match(clean_word, dict_word)
            # print(dict_word,shift,clean_word)
            cnt = 0
            penalty = shift
            while shift > 0:
                cnt += 1
                dict_word = "!" + dict_word
                shift -= 1
            if cnt == 0:
                shift = best_match(dict_word, clean_word)
                penalty = shift
                while shift > 0:
                    dict_word = dict_word + "!"
                    shift -= 1
            sync = _score(dict_word, clean_word)

            for i in range(min(len_word, len(dict_word))):
                scorenow = 0
                if clean_word[i] != ".":
                    continue
                if dict_word[i] == "!" or dict_word[i] == "^" or dict_word[i] == "$":
                    continue
                if dict_word[i] in self.guessed_letters:
                    continue
                start = 4.5
                prev = start
                inc = pow((short_dash) / (len_word), 1.1)
                if sync < 2:
                    continue
                for j in range(i + 1, min(len_word, len(dict_word))):
                    if dict_word[j] == "!":
                        break
                    elif (
                        clean_word[j] == "."
                        and dict_word[j] not in self.guessed_letters
                    ):
                        scorenow = scorenow + pow(prev, 1) / (
                            26 - len(self.guessed_letters)
                        )
                    elif clean_word[j] == dict_word[j]:
                        scorenow = scorenow + pow(prev, 1)
                    prev *= inc
                prev = start
                for j in reversed(range(0, i)):
                    if dict_word[j] == "!":
                        break
                    elif (
                        clean_word[j] == "."
                        and dict_word[j] not in self.guessed_letters
                    ):
                        scorenow = scorenow + pow(prev, 1) / (
                            26 - len(self.guessed_letters)
                        )
                    elif clean_word[j] == dict_word[j]:
                        scorenow = scorenow + pow(prev, 1)
                    prev *= inc
                if dict_word[i] not in score.keys():
                    score.update({dict_word[i]: 0})

                # print(i,scorenow)
                penalty = max(1, penalty)
                sync = max(1, sync)
                score[dict_word[i]] += (
                    (scorenow / pow(penalty, 1)) * pow(7, sync)
                ) * pow(i + 1, 0.65)
                if max_onece < (
                    (scorenow / pow(penalty, 1)) * pow(7 ,sync) * pow(i + 1, 0.65)
                ):
                    max_onece = max(
                        max_onece,
                        ((scorenow / pow(penalty, 1)) * pow(7 ,sync) * pow(i + 1, 0.65)),
                    )
                    max_word = dict_word[i] + "  " + dict_word
        # count occurrence of all characters in possible word matches
        max_score = 0
        max_score_char = "!"
        smax_score_char = "!"
        total = 1
        for ele in score:
            total += score[ele]
            if max_score < score[ele]:
                if ele not in self.guessed_letters:
                    max_score = score[ele]
                    smax_score_char = max_score_char
                    max_score_char = ele
        # print(score)
        print("prob :", end=" ")
        print(max_score / total)
        print("second best char :", end="  ")
        print(smax_score_char)
        print("max score at once is:", end="  ")
        print(max_onece, end="  ")
        print(max_word)
        guess_letter = max_score_char
        # if no word matches in training dictionary, default back to ordering of full dictionary
        print(max_score)
        cnt = 0
        for cha in clean_word:
            if cha != ".":
                cnt += 1
        if guess_letter == "!" or cnt <= (0.2 * (len_word - 2) + 2) and len_word >= 8:
            print("couldnt guess")
            # self.current_dictionary = self.full_dictionary
            newndup = []
            for word in self.ndupdict:
                flag = 0
                for i in range(len(word)):
                    if word[i] in self.guessed_letters:
                        flag = 1
                if flag == 1:
                    continue
                else:
                    newndup.append(word)
            self.ndupdict = newndup
            self.full_dictionary_common_letter_sorted = collections.Counter(
                "".join(self.ndupdict)
            ).most_common()
            sorted_letter_count = self.full_dictionary_common_letter_sorted
            for letter, instance_count in sorted_letter_count:
                if letter not in self.guessed_letters:
                    guess_letter = letter
                    break
        if guess_letter in self.guessed_letters:
            # print("already guessed")
            # self.current_dictionary = self.full_dictionary
            sorted_letter_count = self.full_dictionary_common_letter_sorted
            for letter, instance_count in sorted_letter_count:
                if letter not in self.guessed_letters:
                    guess_letter = letter
                    break
        self.start = 0
        return guess_letter

    ##########################################################
    # You'll likely not need to modify any of the code below #
    ##########################################################

    def build_dictionary(self, dictionary_file_location):
        text_file = open(dictionary_file_location, "r")
        full_dictionary = text_file.read().splitlines()
        text_file.close()
        return full_dictionary

    def start_game(self, practice=True, verbose=True):
        # reset guessed letters to empty set and current plausible dictionary to the full dictionary
        self.guessed_letters = []
        self.current_dictionary = self.full_dictionary
        self.start = 1
        self.ndupdict = []
        for word in self.full_dictionary:
            temp = ""
            for i in range(len(word)):
                if word[i] not in temp:
                    temp += word[i]
            self.ndupdict.append(temp)
        self.full_dictionary_common_letter_sorted = collections.Counter(
            "".join(self.ndupdict)
        ).most_common()

        response = self.request("/new_game", {"practice": practice})
        if response.get("status") == "approved":
            game_id = response.get("game_id")
            word = response.get("word")
            tries_remains = response.get("tries_remains")
            if verbose:
                print(
                    "Successfully start a new game! Game ID: {0}. # of tries remaining: {1}. Word: {2}.".format(
                        game_id, tries_remains, word
                    )
                )
            while tries_remains > 0:
                # get guessed letter from user code
                guess_letter = self.guess(word)
                # print(len(self.current_dictionary))

                # append guessed letter to guessed letters field in hangman object
                self.guessed_letters.append(guess_letter)
                if verbose:
                    print("Guessing letter: {0}".format(guess_letter))

                try:
                    res = self.request(
                        "/guess_letter",
                        {
                            "request": "guess_letter",
                            "game_id": game_id,
                            "letter": guess_letter,
                        },
                    )
                except HangmanAPIError:
                    print("HangmanAPIError exception caught on request.")
                    continue
                except Exception as e:
                    print("Other exception caught on request.")
                    raise e

                if verbose:
                    print("Sever response: {0}".format(res))
                status = res.get("status")
                tries_remains = res.get("tries_remains")
                if status == "success":
                    if verbose:
                        print("Successfully finished game: {0}".format(game_id))
                    return True
                elif status == "failed":
                    reason = res.get("reason", "# of tries exceeded!")
                    if verbose:
                        print(
                            "Failed game: {0}. Because of: {1}".format(game_id, reason)
                        )
                    return False
                elif status == "ongoing":
                    word = res.get("word")
        else:
            if verbose:
                print("Failed to start a new game")
        return status == "success"

    def my_status(self):
        return self.request("/my_status", {})

    def request(self, path, args=None, post_args=None, method=None):
        if args is None:
            args = dict()
        if post_args is not None:
            method = "POST"

        # Add `access_token` to post_args or args if it has not already been
        # included.
        if self.access_token:
            # If post_args exists, we assume that args either does not exists
            # or it does not need `access_token`.
            if post_args and "access_token" not in post_args:
                post_args["access_token"] = self.access_token
            elif "access_token" not in args:
                args["access_token"] = self.access_token

        time.sleep(0.2)

        num_retry, time_sleep = 50, 2
        for it in range(num_retry):
            try:
                response = self.session.request(
                    method or "GET",
                    self.hangman_url + path,
                    timeout=self.timeout,
                    params=args,
                    data=post_args,
                    verify=False,
                )
                break
            except requests.HTTPError as e:
                response = json.loads(e.read())
                raise HangmanAPIError(response)
            except requests.exceptions.SSLError as e:
                if it + 1 == num_retry:
                    raise
                time.sleep(time_sleep)

        headers = response.headers
        if "json" in headers["content-type"]:
            result = response.json()
        elif "access_token" in parse_qs(response.text):
            query_str = parse_qs(response.text)
            if "access_token" in query_str:
                result = {"access_token": query_str["access_token"][0]}
                if "expires" in query_str:
                    result["expires"] = query_str["expires"][0]
            else:
                raise HangmanAPIError(response.json())
        else:
            raise HangmanAPIError("Maintype was not text, or querystring")

        if result and isinstance(result, dict) and result.get("error"):
            raise HangmanAPIError(result)
        return result


class HangmanAPIError(Exception):
    def __init__(self, result):
        self.result = result
        self.code = None
        try:
            self.type = result["error_code"]
        except (KeyError, TypeError):
            self.type = ""

        try:
            self.message = result["error_description"]
        except (KeyError, TypeError):
            try:
                self.message = result["error"]["message"]
                self.code = result["error"].get("code")
                if not self.type:
                    self.type = result["error"].get("type", "")
            except (KeyError, TypeError):
                try:
                    self.message = result["error_msg"]
                except (KeyError, TypeError):
                    self.message = result

        Exception.__init__(self, self.message)


api = HangmanAPI(access_token="e378eb211fd80ea8ca07ba2fd52d79", timeout=2000)
for i in range(10):
    print("i")
    print(i)
    api.start_game(practice=1, verbose=True)
    [
        total_practice_runs,
        total_recorded_runs,
        total_recorded_successes,
        total_practice_successes,
    ] = api.my_status()  # Get my game stats: (# of tries, # of wins)
    print("total wins %d" % (total_practice_successes))
    time.sleep(1)

practice_success_rate = total_practice_successes / total_practice_runs
print(
    "run %d practice games out of an allotted 100,000. practice success rate so far = %.3f"
    % (total_practice_runs, practice_success_rate)
)
