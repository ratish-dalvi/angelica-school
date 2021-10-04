import pandas as pd
from linkage.core.classifier.comparators import person_name_match
from linkage.core.clustering.disjoint_set_clusters import make_disjoint_clusters
from priorityY import priority_based_linkage
import itertools


class Student(object):
    def __init__(self, fn, ln, mn=None):
        self.fn = fn.strip().lower()
        self.ln = ln.strip().lower()
        if mn is not None:
            self.mn = mn.strip().lower()
        else:
            self.mn = mn

    @classmethod
    def parse(cls, name):
        x = name.split()
        fn, ln = x[0], x[-1]
        mn = x[1] if len(x) == 3 else None
        s = cls(fn, ln, mn)

        return s

    def __repr__(self):
        return str(self.fn + " " + self.ln)

    def get_full_name(self):
        if self.mn is not None:
            return " ".join([self.fn, self.mn, self.ln])
        else:
            return " ".join([self.fn, self.ln])


df = pd.read_csv("/tmp/responses_A_fixed.csv")
for col in df.columns:
    x = df[col]
    del df[col]
    df[col.strip()] = x

df['student name'] = df['What is your FIRST name?'] + " " + df['What is your LAST name?']

cols = [
    'Who is ONE other student in your class that you want to work with?',
    'Who is ANOTHER other student in your class that you want to work with?',
    'Who is a THIRD student in your class that you want to work with?',
    'OPTIONAL: Who is a FOURTH student in your section that you want to work with?'
]
# 'OPTIONAL: Is there anyone in this section that you do NOT want to be with?'


def parse_data():
    students = []
    for i, row in df.iterrows():
        s = []
        main_student = Student(row['What is your FIRST name?'], row['What is your LAST name?'])
        s.append(main_student)
        for col in cols:
            name = row[col]
            if pd.notnull(name):
                conn_student = Student.parse(name)
                if conn_student.get_full_name() == main_student.get_full_name():
                    continue
                s.append(conn_student)
        students.append(s)
    return students


def validate_data(students, print_sort=False):
    print("%d elements in list" % len(students))
    x = pd.Series([student.get_full_name() for row in students for student in row])

    print("total students in preferences: %d" % len(x))
    print("Unique students across preferences: %d" % x.nunique())
    print("Most popular kids:\n%s" % x.value_counts().head(3))

    typos = []
    for x1 in x.unique():
        for x2 in x.unique():
            if person_name_match(x1, x2, typo_tolerance=4) and (x1 != x2):
                typos.append(" %s <----->  %s" % tuple(sorted([x1, x2])))

    typos = pd.unique(typos)
    print("%d Potential typos" % len(typos))
    print(typos)
    if print_sort:
        print("\n\nNames in Sorted order")
        for student in x.sort_values().unique():
            print(student)


def make_graph(students):
    student_ids = {}
    max_id = 0
    graph = []
    reverse_student_ids = {}
    for row in students:
        g_row = []
        for student in row:
            if student.get_full_name() in student_ids:
                sid = student_ids[student.get_full_name()]
            else:
                student_ids[student.get_full_name()] = max_id
                reverse_student_ids[max_id] = student.get_full_name()
                sid = max_id
                max_id += 1
            g_row.append(sid)

        graph.append(g_row)
    return graph, student_ids, reverse_student_ids


def group_students(students):
    graph, student_ids, reverse_student_ids = make_graph(students)
    print(graph)
    print(student_ids)
    print(reverse_student_ids)
    clusters = make_disjoint_clusters(graph, len(student_ids))
    print(clusters)
    print(graph)
    G = []

    # Find edge weights
    edge_weights = {}
    for row in graph:
        combinations = list(itertools.combinations(row, 2))
        for edge in combinations:
            if edge[0] == edge[1]:
                continue
            key_edge = "_".join(map(str, sorted(edge)))
            edge_weights[key_edge] = edge_weights.get(key_edge, 0) + 0.5
        main_student = row[0]
        for student in row[1:]:
            edge = (main_student, student)
            key_edge = "_".join(map(str, sorted(edge)))
            edge_weights[key_edge] = edge_weights.get(key_edge, 0) + 0.5

    print(edge_weights)

    # run it again but this time create edges
    visited = {}
    for row in graph:
        combinations = list(itertools.combinations(row, 2))
        for edge in combinations:
            if edge[0] == edge[1]:
                continue
            key_edge = "_".join(map(str, sorted(edge)))
            if key_edge not in visited:
                edge_weight = edge_weights[key_edge]
                if edge_weight >= 3:
                    priority = 1
                elif edge_weight >= 2:
                    priority = 2
                elif edge_weight >= 1:
                    priority = 3
                elif edge_weight == 0.5:
                    priority = 4
                else:
                    raise

                G.append((edge[0], edge[1], priority))
                visited[key_edge] = True

    components = priority_based_linkage(G, threshold=4)
    print("\nGroups: ")
    for row in components:
        print(", ".join([reverse_student_ids[ii] for ii in row]))

    student_matches = {}
    # get all student matches:
    for row in components:
        combinations = list(itertools.combinations(row, 2))
        for edge in combinations:
            student_matches["%s-%s" % (edge[0], edge[1])] = True
            student_matches["%s-%s" % (edge[1], edge[0])] = True

    print("\nStudents whose asks were not met:")
    for row in graph:
        if len(row) == 1:
            continue
        main_student = row[0]
        for student in row[1:]:
            key = "%s-%s" % (main_student, student)
            if key not in student_matches:
                print(reverse_student_ids[main_student], " -> ", reverse_student_ids[student])

# parse data as list of lists
students = parse_data()
validate_data(students)
group_students(students)
