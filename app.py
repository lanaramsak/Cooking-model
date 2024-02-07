import json
import random
import itertools
from collections import Counter

RECIPE = "recipe_goulash" 
#"recipe_potato_salad"
#"recipe_cake"
#"recipe_goulash" 
#recipe_goulash2 is without the required_task-prerequisites to test the different orders

TIME_CHANGE_FACTOR = 5 #meaning a cook can either be quicker/take longer of the max of 10 seconds

class Cooking(object):

    def __init__(self, recipe):
        self.tasks_completed = []
        self.order = []

        # loading resource pool (all available items)
        with open('data/resources.json') as f:
            resources = json.load(f)
            #so that resources we have two of are written twice
            self.resources = []
            for res in resources:
                self.resources += [res["id"]] * res["num"]

        # loading tasks
        with open(f'data/{recipe}.json') as f:
            self.alltasks = json.load(f) #this one does not change throughout the program 
        
        self.tasks_list = self.alltasks.copy()
        
            
class DiscreteEventSimulator:
    def __init__(self):
        self.event_queue = []
        self.cooking = Cooking(RECIPE)
        self.time = 0

    def run_simulation(self):
        self.find_task()
        #this way the simulation end when all tasks are completed and not when the task list is empty
        while len(self.cooking.tasks_completed) != len(self.cooking.alltasks):
            #searching if there are any scheduled events
            if self.event_queue:
                events_at_time_t = [] 
                for x in self.event_queue:
                    #if the task has finnished at current time
                    if x["time"] == self.time:
                        events_at_time_t.append(x)
                for event in events_at_time_t:
                    self.end_task(event["data"])
                    self.event_queue.remove(event)
            #print(f"TIME: {self.time}")
            self.time += 1

            #to stop it in case something goes wrong
            if self.time == 1000:
                break
        #print(f"TIME: {self.time}")
        return (self.time, self.cooking.order)

    def find_task(self):
        #print("searching.....")
        for task in self.cooking.tasks_list:
            if set(task["required_task-prerequisites"]).issubset(set(self.cooking.tasks_completed)) and set(task["required_resources"]).issubset(self.cooking.resources):
                self.start_task(task["name"])
                self.cooking.order.append(task["name"])
                self.find_task()
    
    def start_task(self, task_name):
        #rint(f"doing {task_name} ....")
        #we search for the task in the list of tasks, to be able to get the other data about it
        task = find(self.cooking.alltasks, task_name)

        #running the task
        duration = task["duration"]
        #print(f" removing {task['required_resources']} ")
        for x in task["required_resources"]:
            self.cooking.resources.remove(x)
        self.cooking.tasks_list.remove(task)

        #scheduling the end task event

        #no time randomness
        #self.schedule_end_task(self.time + duration, task_name)

        #with random delays/done quicker
        self.schedule_end_task(self.time + time_randomness(duration), task_name)

    def schedule_end_task(self, event_time, task_name):
        event = {"time": event_time, "data": task_name}
        #print(f"scheduling {event}")
        self.event_queue.append(event)

    def end_task(self, task_name):
        #print(f"ending {task_name}")
        #we search for the task in the list of tasks, to be able to get the other data about it
        task = find(self.cooking.alltasks, task_name)


        #returning resources and adding the task to the finished tasks
        self.cooking.resources += task["required_resources"]
        self.cooking.tasks_completed.append(task_name)
        self.find_task()

    def check_resources(self):
        all_resources = []
        for task in self.cooking.alltasks:
            all_resources += task["required_resources"] 
        if list(set(all_resources)) != list(set(self.cooking.resources)):
            raise ValueError("You don't have the right resources.")


def run(permutations):
    #we go through all permutations and run the simulation for each of them,
    #then the final product is put in a list of pairs, sorted based on the first component (time)
    values = []
    for perm in permutations:
        simulator = DiscreteEventSimulator()
        simulator.check_resources()
        poskus = list(perm)
        #poskus.reverse()
        simulator.cooking.tasks_list = poskus
        value = simulator.run_simulation()

        if value not in values:

            values.append(value)
    values.sort()
    print([value[0] for value in values])

    #the first one will have the shortest time, therefore the best order
    return values[0]

def all_permutations(recipe):
    #getting the list of task to make different permutations
    with open(f'data/{recipe}.json') as f:
            alltasks = json.load(f)
    
    return list(itertools.permutations(alltasks))

def smart_permutations(recipe):
    #getting the list of task
    with open(f'data/{recipe}.json') as f:
            alltasks = json.load(f)    

    #we go through the list of tasks and take out the names of required_task-prerequisites
    required_task_names = []
    for task in alltasks:
        required_task_names += task["required_task-prerequisites"] 

    #here we get a list of pairs ex. [("cutting meat", 1), ("heating water", 2), ...] the number is fo how many times they are needed
    required_tasks_counted = sorted(Counter(required_task_names).items(), key=lambda item: item[1])
    required_tasks_counted.reverse() #to first get the one that is most needed

    #split them based on number of appearnces, permutate each group and add to list seperate_lists
    #find_task is added to get actual tasks, not task names
    k = required_tasks_counted[0][1]
    seperate_lists = []
    for i in range(1,k+1):
        #make nicer later
        count_list = [ find(alltasks, x) for (x, y) in required_tasks_counted if y == i]
        permuted_group = list(itertools.permutations(count_list))
        seperate_lists.append(permuted_group)
        seperate_lists.reverse() #reversed because range goes from 1 -> k which will be from one mentioned to more mentioned

    #we need to get a list of all the tasks that we don't have in the required_tasks
    not_required_tasks = [task for task in alltasks if task["name"] not in required_task_names]
    permuted_group_tasks = list(itertools.permutations(not_required_tasks))

    #getting it all together
    seperate_lists.append(permuted_group_tasks)

    #getting all combinations
    #[[[0, 1], [1, 0]], [[2, 3], [3, 2]]] ---->  [([0, 1], [2, 3]), ([0, 1], [3, 2]), ([1, 0], [2, 3]), ([1, 0], [3, 2])]
    result = list(itertools.product(*seperate_lists))

    #we still need to combine the lists into one
    #[([0, 1], [2, 3]), ([0, 1], [3, 2]), ([1, 0], [2, 3]), ([1, 0], [3, 2])] ----> [[0, 1, 2, 3], [0, 1, 3, 2], [1, 0, 2, 3], [1, 0, 3, 2]]
    def to_list(element):
        element_list = []
        for i in element:
            element_list += i
        return element_list
    
    permutations = [to_list(element) for element in result]
    return permutations


def find(list_of_tasks, task_name):
    #searches for the task in the list of tasks (with other data)
    for i in list_of_tasks:
        if i["name"] == task_name:
            return i
        

def time_randomness(duration):
    #since cooking doesn't always go as planned, we added some randomness, by prolonging/shortening the duration of tasks
    #this is called when scheduling a task and calculating the time it will be completed

    time_random = random.randrange(max( duration - TIME_CHANGE_FACTOR, 2), duration + TIME_CHANGE_FACTOR)
    return time_random

#TODO - function that checks if we have all resources
#run at the start of run


#Getting the best time and order, by trying all permutations
print(run(all_permutations(RECIPE)))


#Getting the best time and order, by not trying all permutations
#print(run(smart_permutations(RECIPE)))


#Used for testing the execution of one recipe, helps to uncomment the print functions in the code
#simulator = DiscreteEventSimulator()
#value = simulator.run_simulation()
#print(value)

