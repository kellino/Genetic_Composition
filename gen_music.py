import random
import scikits.audiolab as alb
from scipy import stats
import numpy as np
from pydub import AudioSegment, playback

second = 1000


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
        # hard coded subdivision of sample. It would be nice to do this
        # programmatically
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
        'Create an individual "member" of the population'
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
        'Create a number of individuals, ie a population'
        return np.array([self.individual(words) for x in xrange(count)])

    def get_skew(self, population):
        return stats.skew(np.array([x.duration_seconds for x in population]))

if __name__ == '__main__':
    wg = WhiteNoiseGen()
    smp = Sampler()
    comp = Composer()
    segment = smp.get_sample('./I will give my love an apple.ogg')
    words = smp.split_sample(segment)
    skews = []
    skews.append(stats.skew(np.array([x.duration_seconds for x in words])))
    playback.play(segment[2000:10000])
    population = comp.population(3)
    for pop in population:
        skews.append(comp.get_skew(pop))
        for p in pop:
            playback.play(p)
    playback.play(segment[2000:25500].fade_out(500))

    print skews
