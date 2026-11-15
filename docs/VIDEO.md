# Запись видео с запуском четырёх реализаций и экспериментов

Запись включает действия в терминале и реальные результаты запусков. При показе старых результатов необходимо обозначить, что это ранее выполненная серия. Для полного повторения экспериментов задания запускаются заново и используются их новые номера.

## 1. Подготовка записи

Открыть PowerShell, увеличить шрифт, убрать с экрана посторонние окна. Включить запись окна доступной программой записи экрана. В Windows можно попробовать Win+Alt+R; если сочетание недоступно, использовать установленный рекордер. До основной записи проверить, что окно терминала и текст попадают в короткий пробный ролик.

Войти по SSH под своей кластерной учётной записью. Не показывать содержимое приватного ключа или парольную фразу. Парольные диалоги можно пройти до начала записи.

## 2. Показать кластер и сборку

На управляющем сервере:

```bash
hostname
sinfo
squeue -u "$USER"
module load compiler/gcc/11 mpi/openmpi/4.1.6/gcc/11 python/3.10
source ~/spline-lab/.venv/bin/activate
cd ~/spline-lab
make -B -j3
mkdir -p logs results work
salloc -N1 -p cascade --ntasks=4 --cpus-per-task=1 --time=00:20:00
echo "$SLURM_JOB_ID"
scontrol show hostnames "$SLURM_JOB_NODELIST"
ssh "$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)"
```

После salloc дождаться выделения, затем выполнять оставшиеся команды. Номер задания записать отдельно.

## 3. Запустить четыре реализации и проверить ответы

На выделенном вычислительном узле:

```bash
hostname
module load compiler/gcc/11 mpi/openmpi/4.1.6/gcc/11 python/3.10
source ~/spline-lab/.venv/bin/activate
cd ~/spline-lab
export OMPI_MCA_pml=ob1
export OMPI_MCA_btl=self,vader,tcp
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
python3 scripts/generate.py work/demo.txt --n 129 --case uneven
```

Затем вводить по одной команде, после каждой дожидаясь возвращения приглашения:

```bash
./bin/spline_pthreads work/demo.txt 4 work/demo-pthreads.txt
python3 scripts/check.py work/demo.txt work/demo-pthreads.txt
./bin/spline_openmp work/demo.txt 4 work/demo-openmp.txt
python3 scripts/check.py work/demo.txt work/demo-openmp.txt
mpirun -np 4 ./bin/spline_mpi work/demo.txt 4 work/demo-c-mpi.txt
python3 scripts/check.py work/demo.txt work/demo-c-mpi.txt
mpirun -np 4 python3 src/spline_mpi.py work/demo.txt 4 work/demo-python-mpi.txt
python3 scripts/check.py work/demo.txt work/demo-python-mpi.txt
```

На видео должны быть видны четыре запуска и четыре PASS. Короткое объяснение: «Строится натуральный кубический сплайн. Трёхдиагональная система решается параллельной циклической редукцией. Проверка выполняется по SciPy и условиям гладкости».

## 4. Освободить интерактивные ресурсы

Выйти с вычислительного узла:

```bash
exit
```

В оболочке salloc на управляющем сервере:

```bash
scancel "$SLURM_JOB_ID"
squeue -u "$USER"
```

При истечении выделения проверить очередь и не использовать старый номер задания.

## 5. Повторить эксперименты

Сначала убрать журналы предыдущей серии из каталога logs, сохранив их в отдельной папке. Это предотвращает выбор минимума между старыми и новыми сериями при агрегации:

```bash
cd ~/spline-lab
archive="results/archive-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$archive/logs"
find logs -maxdepth 1 -type f -exec mv -t "$archive/logs" -- {} +
```

Затем отправить две новые серии:

```bash
sbatch slurm/threads.sbatch
sbatch slurm/mpi.sbatch
squeue -u "$USER"
```

Сохранить оба новых номера из Submitted batch job. Далее вместо THREAD_JOB и MPI_JOB подставлять именно эти числа:

```bash
sacct -j THREAD_JOB,MPI_JOB --format=JobID,State,Elapsed,ExitCode -X
tail -n 10 logs/threads-THREAD_JOB.out
tail -n 10 logs/mpi-MPI_JOB.out
```

Ожидание очереди и длительных вычислений можно вырезать из ролика, сохранив кадры отправки, хода выполнения и окончания. В прошлой серии вычисления занимали около двух минут для потоков и пяти с половиной минут для MPI, но новый запуск и очередь могут занять другое время.

## 6. Показать завершение, таблицу и графики

После COMPLETED и ExitCode=0:0 у обоих заданий:

```bash
tail -n 20 logs/threads-THREAD_JOB.err
tail -n 20 logs/mpi-MPI_JOB.err
module load compiler/gcc/11 mpi/openmpi/4.1.6/gcc/11 python/3.10
source ~/spline-lab/.venv/bin/activate
python3 scripts/plot.py
head -n 12 results/benchmark.csv
ls -lh results/benchmark-*.png
```

Скачать results на ноутбук через scp и показать графики. При объяснении использовать значения именно новой серии. Ускорение считается относительно одного исполнителя той же реализации; отсутствие ускорения MPI также является результатом исследования.

Для сдачи обычно достаточно одного ролика, в котором показаны сборка, четыре ручных запуска с проверками, запуск двух серий, их завершение и графики. Требуемую длительность определяет преподаватель. Видео пока не записано.
