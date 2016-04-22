import logging
import random
import numpy as np
from pydub import AudioSegment, playback

SECOND = 1000
DEBUG = True
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


class Sampler:
    def get_ogg_sample(self, filepath):
        segment = AudioSegment.from_ogg(filepath)
        return segment

    def split_sample(self, segment):
        # hard coded subdivision of sample. It would be nice to do
        # this programmatically
        words = {}
        words[7] = segment[0:800]       # pause
        words[0] = segment[2000:2350]   # I
        words[1] = segment[2350:3000]   # will
        words[2] = segment[3000:3900]   # give
        words[3] = segment[4000:5000]   # my
        words[4] = segment[5000:5500]   # love
        words[5] = segment[5500:6100]   # an
        words[6] = segment[6100:7200]   # apple
        return words


class Composer:
    def __init__(self):
        self.sampler = Sampler()
        self.composition = []
        # self.composition = AudioSegment.empty()
        # simple probability matrix based on pitch occurrences in the source
        # material, however the manner in which it is applied to the words
        # themselves is essentially arbitrary
        self.markov = {0 : [0.571, 0.143, 0   , 0  , 0.143, 0  , 0.143],
                       1 : [0.33 , 0    , 0.66, 0  , 0    , 0  , 0]    ,
                       2 : [0    , 0    , 0   , 1  , 0    , 0  , 0]    ,
                       3 : [0    , 0    , 0.33, 0  , 0.66 , 0  , 0]    ,
                       4 : [0.5  , 0.3  , 0   , 0.2, 0    , 0  , 0]    ,
                       5 : [0    , 0    , 0.33, 0  , 0.66 , 0  , 0]    ,
                       6 : [0    , 0    , 0   , 0  , 0    , 0.5, 0.5]}

    def individual(self, words):
        """ Create an individual 'member' of the population """
        words_list = [x for y, x in words.iteritems()]
        random.shuffle(words_list)
        individual = []
        for j in range(len(words_list)):
            if j % 2 == 0:
                individual.append(words_list[j].reverse())
            elif j % 3 == 0:
                individual.append(words_list[j].fade_in(400).fade_out(100))
            else:
                individual.append(words_list[j])
        return individual

    def population(self, words, count):
        """ Create a number of individuals, ie a population """
        return [self.individual(words) for x in xrange(count)]

    def get_skew(self, individual):
        return np.abs(reduce((lambda x, y: x-y), [len(x) for x in individual]))

    def grade(self, population, target):
        mean = np.mean([[x for x in ind] for ind in population], axis=0)
        skew = self.get_skew(mean)
        return self.fitness(skew, target)

    def fitness(self, skew, target):
            """ Measures the fitness of an individual against the 'perfect' target,
                which is the skew of the original sample """
            return np.abs(target - skew)

    def evolve(self, population, target, retain=0.2,
               random_select=0.05, mutate=33):
        # find the skews of each member in the population
        graded = np.array(
            [self.fitness(self.get_skew(individual), target)
             for individual in population])
        if DEBUG:
            logging.debug("population grading {}".format(graded))
        # choose best performing
        max_ind = np.where(graded == graded.max())
        min_ind = np.where(graded == graded.min())
        if DEBUG:
            logging.debug("index of max is {}".format(max_ind))
            logging.debug("index of min is {}".format(min_ind))
        parent = population[max_ind[0][0]]

        if random.randint(0, 100) < mutate:
            parent = parent[:3] + parent[:-1]

        return parent

    def intro(self, words):
        rand = random.randrange(1, 3)
        for i in range(rand):
            for k, word in words.iteritems():
                self.composition.append(word)
        seed = 3
        self.composition.append(words[seed])
        for i in range(49):
            randFloat = random.uniform(0, 1)
            for j in range(len(self.markov[seed])):
                if randFloat < self.markov[seed][j]:
                    self.composition.append(words[j])
                    seed = j
                    if j % 3 == 0:
                        self.composition.append(words[7])
                    break
                else:
                    # because the melody is quite static, it is necessary to
                    # break a strict markovian process every now and again
                    rand = random.randrange(1, 3)
                    seed = (seed + rand) % len(self.markov[seed])
        rand = random.randrange(1, 2)
        for i in range(rand):
            for k, word in words.iteritems():
                self.composition.append(word)

    def compose(self):
        """ the main composition function of the piece,
        cueing the different elements and appending
        them to a list of musical elements, which is
        returned to the play function """
        segment = self.sampler.get_ogg_sample(
            r'./I will give my love an apple.ogg')
        # exposition
        self.composition.append(segment[2000:25000])
        words = self.sampler.split_sample(segment)
        pause = words[7]
        self.composition.append(pause)
        # false development
        self.intro(words)
        # early recap
        self.composition.append(segment[2000:12000])
        # make a default population
        population = self.population(words, 4)
        target = self.get_skew([x for k, x in words.iteritems()])
        logging.debug("target skew is {}".format(target))
        # (d)evolution development
        for individual in population:
            skew = self.get_skew(individual)
            logging.debug([len(x) for x in individual])
            logging.debug("skew is {}".format(skew))
            for p in individual:
                self.composition.append(p)

        parent = self.evolve(population, target)
        while abs(target - skew) > 200:
            for sperm in parent:
                for s in sperm:
                    self.composition.append(s)
                    new_population = parent + population[1:]
                    parent = self.evolve(new_population[:8], target)
            if DEBUG:
                logging.debug(
                    "absolute different {}".format(np.abs(target - skew)))
        # recap
        self.composition.append(
            segment[2000:25000].fade_in(500).fade_out(1000))

    def play(self):
        for segment in self.composition:
            playback.play(segment)


if __name__ == '__main__':
    music = Composer()
    music.compose()
    music.play()
