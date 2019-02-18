all: prune-cons keep-derivable prune-cons-unopt

prune-cons: prune-cons.cpp
	g++ -std=c++11 -O3 -march=native -Wall -Wextra -Werror prune-cons.cpp -o prune-cons

keep-derivable: keep-derivable.cpp
	g++ -std=c++11 -O3 -march=native -Wall -Wextra -Werror keep-derivable.cpp -o keep-derivable

prune-cons-unopt: prune-cons-unopt.cpp
	g++ -std=c++11 -O3 -march=native -Wall -Wextra -Werror prune-cons-unopt.cpp -o prune-cons-unopt

clean:
	rm -f prune-cons prune-cons-unopt keep-derivable
