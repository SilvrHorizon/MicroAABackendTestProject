

with open('worklog.txt') as f:
    nxt = f.readline()
    
    total_in_minutes = 0
    while nxt:
        # print(nxt)

        if len(nxt.split('d=')) > 1:
            second = nxt.split('d=')[1]
            
            hours = int(second.split('h')[0])
            minutes = int(second.split('h')[1].split(':')[0].strip())

            
            total_in_minutes+= hours*60 + minutes

            print(f'{hours}:{minutes}')
        nxt = f.readline()

    print(total_in_minutes)

