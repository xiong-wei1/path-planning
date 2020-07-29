import time

import numpy as np

from scipy.special import comb

import matplotlib.pyplot as plt
import matplotlib.patches as ptc

from geometry import Point, Line, Polygon


class Grid:
    def __init__(self, minimum, maximum, first, final):
        self.minimum = minimum
        self.maximum = maximum
        self.width = maximum.x - minimum.x
        self.height = maximum.y - minimum.y
        self.first = first
        self.final = final

    def generateBoundaries(self, size):
        return [
            Polygon(self.width, size, 0.0, Point(self.minimum.x, self.maximum.y)),
            Polygon(self.width, size, 0.0, Point(self.minimum.x, self.minimum.y - size)),
            Polygon(size, self.height + size * 2.0, 0.0, Point(self.maximum.x, self.minimum.y - size)),
            Polygon(size, self.height + size * 2.0, 0.0, Point(self.minimum.x - size, self.minimum.y - size))
        ]

    def random(self, offset, size):
        return Point(
            np.random.randint(self.minimum.x+offset.x, self.maximum.x-offset.x-size.x+1),
            np.random.randint(self.minimum.y+offset.y, self.maximum.y-offset.y-size.y+1),
        )

    def generateObstacles(self, count, size, theta):
        obstacles = []
        for _ in range(count):
            obstacle = Polygon(size.x, size.y, theta, self.random(Point(0, 0), size))
            while self.first.intersects(obstacle) or self.final.intersects(obstacle):
                obstacle = Polygon(size.x, size.y, theta, self.random(Point(0, 0), size))
            obstacles.append(obstacle)
        return obstacles


class Path:
    def __init__(self, points):
        self.score = np.inf
        self.points = points

    def fitness(self, obstacles, shortest):
        distance = 0
        collisions = 0

        for i in range(len(self.points) - 1):
            segment = Line(self.points[i], self.points[i + 1])
            distance += segment.length
            for obstacle in obstacles:
                if segment.intersects(obstacle):
                    collisions += 1000

        self.score = np.sqrt((distance / shortest.length) ** 2 + collisions ** 2)


def individual(grid, interpolation, segments, size):
    points = [grid.first]

    for s in range(segments):
        nextPoint = grid.random(size, Point(0, 0)) if s < segments-1 else grid.final
        segment = Line(points[-1], nextPoint)
        points.extend(segment.divide(interpolation))

    return points


def bezierCurve(points, samples):
    t = np.linspace(0.0, 1.0, samples)

    px = [p.x for p in points]
    py = [p.y for p in points]

    polynomials = [bernsteinPolynomial(len(points) - 1, i, t) for i in range(len(points))]

    vx = np.dot(px, polynomials)
    vy = np.dot(py, polynomials)

    return [Point(vx[s], vy[s]) for s in range(samples)]


def bernsteinPolynomial(n, i, t):
    return comb(n, i) * (t ** i) * ((1 - t) ** (n - i))


def sort(population):
    if len(population) <= 1:
        return population

    mid = len(population) // 2

    left = sort(population[:mid])
    right = sort(population[mid:])

    return merge(left, right, population.copy())


def merge(left, right, population):
    leftPosition = 0
    rightPosition = 0

    while leftPosition < len(left) and rightPosition < len(right):

        if left[leftPosition].score <= right[rightPosition].score:
            population[leftPosition + rightPosition] = left[leftPosition]
            leftPosition += 1
        else:
            population[leftPosition + rightPosition] = right[rightPosition]
            rightPosition += 1

    for leftPosition in range(leftPosition, len(left)):
        population[leftPosition + rightPosition] = left[leftPosition]

    for rightPosition in range(rightPosition, len(right)):
        population[leftPosition + rightPosition] = right[rightPosition]

    return population


def evolve(population, grid, size, count, chance):
    children = []
    while len(children) < count:
        parentA = np.random.randint(0, len(population))
        parentB = np.random.randint(0, len(population))
        if parentA != parentB:
            pathA = population[parentA].points
            pathB = population[parentB].points
            crossoverPosition = len(pathA) // 2
            child = pathA[:crossoverPosition] + pathB[crossoverPosition:]
            if np.random.random() <= chance:
                mutationPosition = np.random.randint(0, len(child))
                child[mutationPosition] = grid.random(size, Point(0, 0))
            children.append(child)
    return children


def visualize(grid, boundaries, obstacles, title, population=None, optimal=None):
    fig, ax = plt.subplots()

    ax.set_title(title, weight='bold')

    ax.annotate(
        "FIRST", (grid.first.x, grid.minimum.y - 0.1),
        horizontalalignment='center',
        verticalalignment='top',
        weight='bold', color='w',
    )

    ax.annotate(
        "FINAL", (grid.final.x, grid.maximum.y + 0.0),
        horizontalalignment='center',
        verticalalignment='bottom',
        weight='bold', color='w'
    )

    for obstacle in obstacles:
        rectangle = ptc.Rectangle(
            obstacle.datum,
            obstacle.width,
            obstacle.height,
            obstacle.angle(),
            edgecolor='None', facecolor='grey', alpha=1.0
        )
        ax.add_patch(rectangle)

    for boundary in boundaries:
        rectangle = ptc.Rectangle(
            boundary.datum,
            boundary.width,
            boundary.height,
            boundary.angle(),
            edgecolor='None', facecolor='black', alpha=1.0
        )
        ax.add_patch(rectangle)

    if population is not None:
        for path in population:
            px = [point.x for point in path.points]
            py = [point.y for point in path.points]
            ax.plot(px, py, 'y-', alpha=0.2, markersize=4)

    if optimal is not None:
        px = [point.x for point in optimal.points]
        py = [point.y for point in optimal.points]
        ax.plot(px, py, 'c-', alpha=0.8, markersize=4)

    ax.plot(grid.first.x, grid.first.y, 'co')
    ax.plot(grid.final.x, grid.final.y, 'mo')

    ax.grid()

    plt.axis('scaled')
    plt.show()


def scatterPlot(x, y, title, xlabel, ylabel):
    fig, ax = plt.subplots()
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.scatter(x, y, marker='o', c='c')
    plt.grid()
    plt.show()


def main():
    gridMinimum = Point(0.0, 0.0)
    gridMaximum = Point(20.0, 20.0)

    vehicleFirst = Point(2.0, 2.0)
    vehicleFinal = Point(18.0, 18.0)

    grid = Grid(gridMinimum, gridMaximum, vehicleFirst, vehicleFinal)

    objectSize = Point(1.0, 1.0)

    boundaries = grid.generateBoundaries(min(objectSize.x, objectSize.y))

    obstacleCount = 40
    obstacleTheta = 0.0

    obstacles = grid.generateObstacles(obstacleCount, objectSize, obstacleTheta)

    visualize(grid, boundaries, obstacles, "Environment")

    startTime = time.time()

    shortestPath = Line(grid.first, grid.final)

    populationCount = 80
    interpolation = 8
    pathSegments = 2

    curveSamples = 16

    initialPopulation = []

    for _ in range(populationCount):
        path = Path(individual(grid, interpolation, pathSegments, objectSize))
        path.points = bezierCurve(path.points, curveSamples)
        path.fitness(obstacles, shortestPath)
        initialPopulation.append(path)

    gradedPopulation = sort(initialPopulation)

    mutationChance = 0.04
    evolutionCount = 0
    evolutionMax = 10

    finalPopulation = None
    optimalPath = None

    averageFitness = []

    while evolutionCount < evolutionMax:
        evolvedPaths = evolve(gradedPopulation, grid, objectSize, populationCount, mutationChance)

        evolvedPopulation = []

        for points in evolvedPaths:
            path = Path(points)
            path.fitness(obstacles, shortestPath)
            evolvedPopulation.append(path)

        gradedPopulation.extend(evolvedPopulation)
        gradedPopulation = sort(gradedPopulation)

        if len(gradedPopulation) > populationCount:
            gradedPopulation = gradedPopulation[:populationCount]

        average = 0
        for path in gradedPopulation:
            average += path.score
        average /= len(gradedPopulation)

        averageFitness.append(average)

        print(
            "Evolution:", evolutionCount + 1,
            "| Average Fitness:", average,
            "| Best Fitness Value:", gradedPopulation[0].score
        )

        evolutionCount += 1

        if evolutionCount == evolutionMax:
            finalPopulation = gradedPopulation
            optimalPath = gradedPopulation[0]

    endTime = time.time()

    print("Time Elapsed:", endTime - startTime)

    visualize(grid, boundaries, obstacles, "Initial Population", initialPopulation)

    visualize(grid, boundaries, obstacles, "Final Population", finalPopulation)

    visualize(grid, boundaries, obstacles, "Optimal Path", None, optimalPath)

    scatterPlot(
        np.arange(1, evolutionMax + 1), averageFitness,
        "Average Fitness of Population", "Evolution", "Fitness Value"
    )

    # input("Press Enter to Exit")


if __name__ == "__main__":
    main()
