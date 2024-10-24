import pstats

p = pstats.Stats('profile_results.prof')
p.sort_stats('cumtime').print_stats(10)