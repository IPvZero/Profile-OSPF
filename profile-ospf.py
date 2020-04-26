import os
import subprocess
import colorama
from colorama import Fore, Style
from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result, print_title
from nornir.plugins.tasks.networking import netmiko_send_config
from nornir.plugins.tasks.data import load_yaml
from nornir.plugins.tasks.text import template_file


nr = InitNornir(config_file="config.yaml")
def clean_ospf(task):
    r = task.run(task=netmiko_send_command, command_string = "show run | s ospf")
    output = r.result
    num = [int(s) for s in output.split() if s.isdigit()]
    for x in num:
        if x == 0:
            continue
        task.run(task=netmiko_send_config, config_commands=["no router ospf " + str(x)])

    desired_ospf(task)


def desired_ospf(task):
    data = task.run(task=load_yaml,file=f'./host_vars/{task.host}.yaml')
    task.host["OSPF"] = data.result["OSPF"]
    r = task.run(task=template_file, template="ospf.j2", path="./templates")
    task.host["config"] = r.result
    output = task.host["config"]
    send = output.splitlines()
    task.run(task=netmiko_send_config, name="OSPF Desired State", config_commands=send)


current = "pyats learn ospf --testbed-file testbed.yaml --output ospf-current"
os.system(current)
command = subprocess.run(["pyats", "diff", "desired-ospf/", "ospf-current", "--output", "ospfdiff"], stdout=subprocess.PIPE)
stringer = str(command)
if "Diff can be found" in stringer:
    clear_command = "clear"
    os.system(clear_command)
    print(Fore.CYAN + "#" * 70)
    print(Fore.RED + "ALERT: " + Style.RESET_ALL + "CURRENT OSPF CONFIGURATIONS ARE NOT IN SYNC WITH DESIRED STATE!")
    print(Fore.CYAN + "#" * 70)
    print("\n")
    answer = input(Fore.YELLOW + "Would you like to reverse the current OSPF configuration back to its desired state? " + Style.RESET_ALL + "<y/n>: ")
    if answer == "y":
        def main() -> None:
            clear_command = "clear"
            clean_up = "rm -r ospfdiff ospf-current"
            os.system(clean_up)
            os.system(clear_command)
            nr = InitNornir(config_file="config.yaml")
            output = nr.run(task=clean_ospf)
            print_title("REVERSING OSPF CONFIGURATION BACK INTO DESIRED STATE")
            print_result(output)

        if __name__ == '__main__':
                main()

else:
    clean_up = "rm -r ospfdiff ospf-current"
    os.system(clean_up)
    print("\n")
    print("~" * 50)
    print(Fore.GREEN + "Good news! OSPF configurations are matching desired state!" + Style.RESET_ALL)
    print("~" * 50)
