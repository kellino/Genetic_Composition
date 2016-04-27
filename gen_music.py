#!/usr/bin/python3.5
import logging
import random
import numpy as np
from os import path
from sys import exit
from collections import namedtuple
from pydub import AudioSegment as AS
from pydub import playback as pb
from pydub import effects as ef
from functools import reduce

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


class Sampler:
    def get_ogg_sample(self, filepath):
        if path.exists(filepath):
            segment = AS.from_ogg(filepath)
            return segment
        else:
            logging.debug("Unable to find file {}".format(filepath))
            exit(1)

    def get_wav_sample(self, filepath):
        if path.exists(filepath):
            segment = AS.from_wav(filepath)
            return segment
        else:
            logging.debug("Unable to find file {}".format(filepath))
            exit(1)

    def split_sample(self, segment):
        """splits the selected piece of audio into different sections
           storing them in a dictionary"""
        chunk = namedtuple('chunk', 'text rank section')
        words = {}
        words[0] = chunk('i', 0.35, segment[2000:2350])
        words[1] = chunk('will', 0.65, segment[2350:3000])
        words[2] = chunk('give', 0.9, segment[3000:3900])
        words[3] = chunk('my', 1.0, segment[4000:5000])
        words[4] = chunk('love', 0.5, segment[5000:5500])
        words[5] = chunk('an', 0.6, segment[5500:6100])
        words[6] = chunk('apple', 1100, segment[6100:7200])
        return words


class Composer:
    def __init__(self):
        self.sampler = Sampler()
        # stores the in-progress composition
        self.composition = []
        # the probability matrix started as a quite literal reading of pitch probability
        # but this led to an intolerable amount of repetition, so this is rather more
        # hand-crafted
        self.markov = {0 : [0, 0.33, 0.18, 0, 0.143, 0.2, 0.143],
                       1 : [0.3, 0, 0.6, 0, 0.1, 0, 0],
                       2 : [0, 0.1, 0.33, 0.3, 0, 0.28, 0],
                       3 : [0.2, 0, 0.2, 0.33, 0.15, 0.12, 0],
                       4 : [0.24, 0.3, 0, 0.2, 0.26, 0, 0],
                       5 : [0.2, 0, 0.32, 0, 0.48, 0, 0],
                       6 : [0, 0, 0.25, 0, 0.25, 0, 0.5]
                      }

    def individual(self, words):
        """ generate a randomized member of population """
        wordlist = [v for k, v in words.items()]
        random.shuffle(wordlist)
        individual = []
        for i in range(len(wordlist)):
            if i % 2 == 0:
                wordlist[i].section.reverse()
                individual.append(wordlist[i])
            elif i % 3 == 0:
                wordlist[i].section.fade_in(400).fade_out(100)
                individual.append(wordlist[i])
            else:
                individual.append(wordlist[i])
        return individual

    def population(self, words, count):
        return [self.individual(words) for x in range(count)]

    def get_deviation(self, individual):
        """ deviation of member of population """
        return np.abs(reduce((lambda x, y: x - y), [x.rank for x in individual]))

    def fitness(self, target, deviation):
        return np.abs(target - deviation)

    def grade(self, population, target):
        """ deviation of the population as a whole. """
        mean = np.mean([self.get_deviation(x) for x in population])
        mean = np.round(mean)
        return self.fitness(target, mean)

    def mutate(self, population, target, extinct=20, mutate=40):
        # first find the fitness levels of each member of the population
        graded = [self.get_deviation(x) for x in population]
        graded = [self.fitness(target, d) for d in graded]

        rand = random.randint(0, 100)

        if rand > extinct:
            # find the member of the population with the best fitness
            # (ie, the one with the smallest
            # deviation from the target)
            fittest_index = graded.index(min(graded))
            fittest = population[fittest_index]
        else:
            # the fittest can sometimes die out, through no real
            # fault of its own. Let's factor that in
            # and assume that the least similar - ie the most
            # genetically diverse - manages to survive
            fittest_index = graded.index(max(graded))
            fittest = population[fittest_index]

        # mutation may or may not occur between generations, and
        # may be benficial, or not...
        rand = random.randint(0, 100)

        if rand < mutate:
            # individual expects a dictionary, so let's convert our
            # fittest member back to this form
            words = {i: fittest[i] for i in range(0, len(fittest))}
            fittest = self.individual(words)
            # replace the previous fittest with the new fittest
            population[fittest_index] = fittest

        return population

    def markov_chain(self, words, seed=3):
        # add the seed, defaults to apple
        self.composition.append(words[seed].section)
        for i in range(27):
            randFloat = random.uniform(0, 1)
            temp = sorted(self.markov[seed])
            for j in range(len(temp)):
                if randFloat <= temp[j]:
                    index = self.markov[seed].index(temp[j])
                    seed = index
                    logging.debug("seed is {}".format(seed))
                    break
            self.composition.append(words[seed].section)

    def get_original(self):
        segment = self.sampler.get_ogg_sample(
            r'./I will give my love an apple.ogg')
        words = self.sampler.split_sample(segment)
        return segment, words

    def introduction(self, original, words, repeat=20):
        # original, words = self.get_original()
        self.composition.append(original[2000:25000])

        rand = random.randint(2, 4)
        wordlist = [v.section for k, v in words.items()]
        for i in range(rand):
            for word in wordlist:
                if i == 0:
                    self.composition.append(word)
                else:
                    new_rand = random.randint(0, 100)
                    if new_rand < repeat:
                        self.composition.append(word)
                        self.composition.append(word)
                    else:
                        self.composition.append(word)
        # repeat the original again just to cement it in the brain
        for word in wordlist:
            self.composition.append(word)

    def add_population(self, population):
        for i in population:
            for segment in i:
                self.composition.append(segment.section)

    def play(self):
        for chunk in self.composition:
            pb.play(chunk)

    def main(self):
        # get original sample
        original, words = self.get_original()
        # generate exposition
        self.introduction(original, words)
        target = self.get_deviation([x for k, x in words.items()])
        logging.debug("target is {}".format(target))
        # pseudo-development
        self.markov_chain(words)
        # false recapitulation
        self.composition.append(original[2500:16000])
        # start mutation
        pop = self.population(words, 4)
        self.add_population(pop)
        pop = self.mutate(pop, target)
        grd = self.grade(pop, target)
        # loop until grade approaches our target (here 4.5) or
        # until a certain number of iterations have completed. This is
        # only to ensure the algorithm runs in 'reasonable' time
        i = 0
        while grd < 4.5 and i < 3:
            pop = self.mutate(pop, target)
            self.add_population(pop)
            grd = self.grade(pop, target)
            i += 1
        phased = [ef.invert_phase(x) for x in self.composition[-20:-1]]
        self.composition += phased
        self.composition.append(original[2000:25000].fade_in(100).fade_out(1000))
        # play everything
        self.play()

if __name__ == '__main__':
    music = Composer()
    music.main()
