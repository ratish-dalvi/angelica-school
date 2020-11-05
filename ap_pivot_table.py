import pandas as pd

# Download sheet
PATH = "~/Downloads/AP Tracker_Rosters 2020-2021.xlsx"
AP_CLASSES = [
    "Language", "US History", "Psych", "Environmental Science",
    "Statistics", "Government & Politics"
]

dfs = {}

students = set()
for sheet_name in AP_CLASSES:
    df = pd.read_excel(PATH, sheet_name=sheet_name)

    print(df.head())
    students.update(df["Name"].tolist())

    df['cleaned_name'] = df.Name.apply(lambda x: x.lower().strip())
    df.set_index('cleaned_name', inplace=True)

    dfs[sheet_name] = df

print("Students: %s" % (students))
print("Total students: %s" % len(students))

cleaned_students = set([x.lower().strip() for x in students])
if len(cleaned_students) != len(students):
    print("potential duplicate student names found")


rows = []

for student in students:
    clean_name = student.lower().strip()
    record = {'Name': student, 'num_ap_classes': 0, 'iep': None, 'enl': None}
    for sheet_name in AP_CLASSES:
        df = dfs[sheet_name]
        try:
            X= df.loc[clean_name]
            record[sheet_name] = 'X'
            record['num_ap_classes'] += 1
            record['grade'] = X['Grade']
            if record['iep'] is None:
                if X['IEP'] is not None and (X['IEP'].strip() not in ['x', 'X']):
                    raise Exception("student '%s' has IEP marked as '%s'" % (student, X['IEP']))
                if X['IEP'] is not None:
                    record['iep'] = X['IEP']

            if record['enl'] is None:
                if X['ENL'] is not None and (X['ENL'].strip() not in ['x', 'X']):
                    raise Exception("student '%s' has ENL marked as '%s'" % (student, X['ENL']))
                if X['ENL'] is not None:
                    record['enl'] = X['ENL']

        except:
            pass
    rows.append(record)

df = pd.DataFrame(rows)

df.to_csv("~/Desktop/ap_pivot_table.csv")
print(df)
