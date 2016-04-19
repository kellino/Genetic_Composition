import logging
import random
import scikits.audiolab as alb
from scipy import stats
import numpy as np
from pydub import AudioSegment, playback

SECOND = 1000
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


class WhiteNoiseGen:
    def individual(self, length):
        return [np.random.uniform(-1, 1, length)]

    def play_individual(self, individual, coeff):
        scaled = np.int16(individual / np.max(np.abs(individual)) * coeff)
        alb.play(scaled)


class Sampler:
    def get_sample(self, filepath):
        segment = AudioSegment.from_ogg(filepath)
        return segment

    def split_sample(self, segment):
        # hard coded subdivision of sample. It would be nice to do this programmatically
        words = []
        pause = segment[0:800]
        words.append(pause)
        i = segment[2000:2350]
        words.append(i)
        will = segment[2350:3000]
        words.append(will)
        give = segment[3000:4000]
        words.append(give)
        my = segment[4000:5000]
        words.append(my)
        love = segment[5000:5500]
        words.append(love)
        a = segment[5500:6000]
        words.append(a)
        return words


class Composer:
    def individual(self, words):
        """ Create an individual 'member' of the population """
        rands = [random.randrange(1, 6, 1) for _ in range(3)]
        sorted(rands)
        individual = []
        random.shuffle(words)
        for j in range(len(words)):
            if j % rands[0] == 0:
                individual.append(words[j].reverse())
            if j % rands[1] == 0:
                individual.append(words[j].fade_in(400).fade_out(100))
            if j+j % rands[2] == 0:
                rand = random.randint(1000, 100000)
                ind = wg.individual(rand)
                coeff = random.randint(1000, 100000)
                wg.play_individual(ind, coeff)
            else:
                individual.append(words[j])
        return individual

    def population(self, count):
        """ Create a number of individuals, ie a population """
        return np.array([self.individual(words) for x in xrange(count)])

    def get_skew(self, individual):
        return stats.skew(np.array([x.duration_seconds for x in individual]))

    def fitness(self, skew, target):
        """ Measures the fitness of an individual against the 'perfect' target,
            which is the skew of the original sample """
        return np.abs(target - skew)

    def grade(self, population, target):
        summation = np.sum([[x for x in ind] for ind in population], axis=0)
        skew = self.get_skew(summation)
        return self.fitness(skew, target)

    def evolve(self, population, target, retain=0.2, random_select=0.05, mutate=10):
        # find the skews of each member in the population
        graded = np.array([self.fitness(self.get_skew(individual), target) for individual in population])
        # logging.debug("population grading {}".format(graded))
        # choose best performing
        max_ind = np.where(graded == graded.max())
        min_ind = np.where(graded == graded.min())
        # logging.debug("index of max is {}".format(max_ind))
        # logging.debug("index of min is {}".format(min_ind))
        parent1 = population[max_ind]
        parent2 = population[min_ind]

        if mutate > random.randint(0, 100):
            parent1 = parent1[:3] + parent1[:-1]

        return parent1 + parent2


if __name__ == '__main__':
    wg = WhiteNoiseGen()
    smp = Sampler()
    comp = Composer()
    segment = smp.get_sample('./I will give my love an apple.ogg')
    words = smp.split_sample(segment)
    target = stats.skew(np.array([x.duration_seconds for x in words]))
    playback.play(segment[2000:10000])
    # create an initial population. In this case, _ grandparents
    population = comp.population(4)
    # used for debugging purposes
    fitnesses = []
    for individual in population:
        skew = comp.get_skew(individual)
        fitnesses.append(comp.fitness(skew, target))
        for p in individual:
            playback.play(p)
    # play final, correct version

    # logging.debug("target = {}".format(target))
    # logging.debug(comp.grade(population, target))
    # for i in range(len(fitnesses)):
        # logging.debug("individual {} has fitness {}".format(i+1, fitnesses[i]))

    parent = comp.evolve(population, target)
    skew = comp.grade(parent, target)
    while np.abs(target - skew) > 0.05:
        for sperm in parent:
            for s in sperm:
                playback.play(s)
        parent = comp.evolve(population, target)
        skew = comp.grade(parent, target)
        logging.debug(np.abs(target - skew))
    playback.play(segment[2000:25500].fade_out(500))
