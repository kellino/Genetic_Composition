-- dirt simple markov matrix calculator, done in haskell for no good reason

import Data.Function

fDiv = (/) `on` fromIntegral

markov :: [Int] -> [Float]
markov xs = map (\x -> x `fDiv` (sum xs)) xs

markov_matrix :: [[Int]] -> [[Float]]
markov_matrix  = map markov
