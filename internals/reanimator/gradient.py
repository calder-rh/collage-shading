from typing import Union, Any, Callable, List, Set, Tuple, Dict
from random import uniform

Num = Union[int, float]
Pair = Tuple[Num, Num]
Values = List[Num]


def norm(l: List[Num]):
	"""
	Calculates the length of the vector l using Pythagorean theorem.
	"""
	return sum(e ** 2 for e in l) ** 0.5


def gradientDescent(lossFunction: Callable[[Values], Num],
					startValues: Values,
					startStep=None,
					delta=None,
					threshold=None,
					maxIterations=None):
	"""
	Uses the gradient descent algorithm to attempt to find the target location.

	At the target location, the loss function will be 0, and at other locations, it will be >0. The
	algorithm starts in one location and takes a series of steps that bring it closer to the
	target. In each iteration, it finds the slope of the loss function around its current location,
	and takes a step in whatever direction the loss function decreases most steeply.

	Arguments:
		lossFunction: a loss function from createFunctions. The target values and instance maker
			are all wrapped up in here. Technically, this could be any function that takes in a
			list of numbers and outputs a nonnegative number. The goal is to find the values that
			make this function output 0.
		startValues: the values to start gradient descent from

	Optional keyword arguments (tweak these if it’s not working):
		startStep: how big of a step is taken at each iteration of the algorithm, initially. This
			value may change later on as it narrows down to a solution.
			If it’s too large, it may overshoot the solution.
			If it’s too small, it may take a long time to get there.
		delta: at each iteration, the algorithm calculates the loss function at the current
			location, and also at other locations very close to it — the locations delta away along
			each axis. This tells it which direction the loss function decreases most rapidly, so
			it can take a step in that direction.
			If it’s too large, the slope calculated will be less accurate, since the points used to
				calculate the slope are farther apart.
			If it’s too small, the slope calculated may be less accurate: some measurements are
				automatically rounded (e.g. bounding box width), and if the algorithm samples two
				locations that are too close, such measurements can be rounded to the same value.
				This makes the algorithm think that those measurements don’t change at all when it
				moves in any direction, so it doesn’t know how to make those measurements closer to
				the right value.
		threshold: how small the loss has to get (i.e. how close the measurements have to get to
			the target) for the function to say it’s close enough and return the current location.
		maxIterations: if the loss never goes below the threshold, it will return the current
			location after this many iterations anyway to prevent it from taking too long or going
			in an infinite loop.

	Returns:
		The values found
		The loss function at that Location
	"""

	# Set default values
	if startStep is None:
		startStep = 0.1
	if delta is None:
		delta = 0.001
	if threshold is None:
		threshold = 0.0001
	if maxIterations is None:
		maxIterations = 100

	numValues = len(startValues)
	currentValues = startValues
	stepSize = startStep
	lossHistory = []

	for i in range(maxIterations):
		# print(i)
		# Calculate the current loss (in this context, the distance to the target measurements)
		currentLoss = lossFunction(currentValues)

		# If it’s below the desired threshold, return it immediately
		if currentLoss <= threshold:
			return currentValues, currentLoss

		# Keep track of the loss of each place tried
		lossHistory.append(currentLoss)

		# If the most recent step increased the loss, then we probably overshot and the step size should be decreased
		if len(lossHistory) >= 2 and lossHistory[-1] > lossHistory[-2]:
			stepSize *= 0.8

		# If the last 5 steps decreased the loss, it might still be a while until we get to the target and the step size should be increased
		minimumMonotony = 5
		if len(lossHistory) > minimumMonotony:
			isMonotonous = True
			for i in range(-minimumMonotony, 0):
				if lossHistory[i] > lossHistory[i - 1]:
					isMonotonous = False
					break
			if isMonotonous:
				stepSize *= 1.1

		# Calculate the gradient (the slope in each direction)
		gradient = []
		# For each value that can be changed (each “direction”)
		for valueIndex in range(numValues):
			# Calculate the loss for an instance where this value is tweaked a bit but everything else is the same
			currentPlusDeltaValues = currentValues.copy()
			currentPlusDeltaValues[valueIndex] += delta
			currentPlusDeltaLoss = lossFunction(currentPlusDeltaValues)
			# Calculate the slope based on that
			partial = (currentPlusDeltaLoss - currentLoss) / delta
			gradient.append(partial)

		# The gradient determines the opposite of the direction to go in
		# To find the step to take, reverse the direction and normalize this so it’s the right length
		gradientNorm = norm(gradient)
		step = gradient
		if gradientNorm != 0:
			step = [e * (-stepSize / gradientNorm) for e in gradient]

		# Change the current values by the amounts determined by the step
		for valueIndex in range(numValues):
			currentValues[valueIndex] += step[valueIndex]

	return currentValues, currentLoss